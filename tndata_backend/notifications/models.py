import json
import logging
import pytz

from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from jsonfield import JSONField
from pushjack import GCMClient
from goals.settings import (
    DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE
)

from . managers import GCMMessageManager
from . settings import GCM
from . signals import notification_snoozed

logger = logging.getLogger("loggly_logs")


class GCMDevice(models.Model):
    """A User's registered device."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="The owner of this message."
    )
    device_name = models.CharField(
        max_length=32,
        blank=True,
        default="Default Device",
        help_text="A name for this device"
    )
    device_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Some unique ID for a device. This is used to help update "
                  "the registration_id for individual users."
    )
    registration_id = models.CharField(
        max_length=256,
        db_index=True,
        help_text="The Android device ID"
    )
    is_active = models.BooleanField(
        default=True,
        blank=True,
        help_text="Does this device accept notifications?"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', '-created_on', 'registration_id']
        unique_together = ("registration_id", "user")
        verbose_name = "GCM Device"
        verbose_name_plural = "GCM Devices"

    def __str__(self):
        return self.device_name or self.registration_id


class GCMMessage(models.Model):
    """A Notification Message sent via GCM."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="The owner of this message."
    )
    title = models.CharField(max_length=256, default="")
    message = models.CharField(max_length=256, default="")

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Successful deliver? True/False, Null == message not sent.
    success = models.NullBooleanField(
        help_text="Whether or not the message was delivered successfully"
    )
    response_code = models.IntegerField(blank=True, null=True)
    response_text = models.TextField(
        blank=True,
        help_text="text of the response sent to GCM."
    )
    response_data = JSONField(
        blank=True,
        default={},
        help_text="The response data we get from GCM after it delivers this"
    )
    registration_ids = models.TextField(
        blank=True,
        help_text="The registration_ids that GCM says it delivered to",
    )
    deliver_on = models.DateTimeField(
        db_index=True,
        help_text="Date/Time on which the message should be delivered (UTC)"
    )
    expire_on = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date/Time when this should expire (UTC)"
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0} on {1}".format(self.title, self.deliver_on)

    class Meta:
        ordering = ['-success', 'deliver_on', '-created_on']
        unique_together = ("user", "title", "message", "deliver_on")
        verbose_name = "GCM Message"
        verbose_name_plural = "GCM Messages"

    def _set_deliver_on(self, dt):
        """Set a new deliver on date using the given datetime object. If
        the given datetime object is naive, it will be converted to the user's
        timezone (if available), then converted to UTC and stored. This method
        will set the value of the `devliver_on` field.

        Returns True if the field was updated.

        """
        if timezone.is_naive(dt):
            # Convert to user's timezone if possible.
            if self.user and hasattr(self.user, "userprofile"):
                tz = pytz.timezone(self.user.userprofile.timezone)
                dt = timezone.make_aware(dt, timezone=tz)

            # Convert to UTC before saving.
            dt = dt.astimezone(timezone.utc)
        self.deliver_on = dt
        return True

    def _snooze_hours(self, hours):
        """If we're snoozing a set number of hours, this method will calculate
        that and update the `deliver_on` field appropriately.

        Returns True if the field was updated.

        """
        changed = False
        if hours is not None and isinstance(hours, list) and len(hours) > 0:
            hours = hours[0]  # if it's a list, pluck the first element
        if hours is not None and isinstance(hours, str):
            try:
                hours = int(hours)  # convert to an int
            except ValueError:
                hours = None
        if hours:
            self.deliver_on = timezone.now() + timedelta(hours=hours)
            changed = True
        return changed

    def snooze(self, hours=None, new_datetime=None, save=True):
        """Snoozing a message essentially reschedules it for delivery at another
        time. This involves:

        - resetting the message's deliver_on date/time.
        - removing the expire_on field.
        - removing the success value (success=True gets excluded by the
          manager's ready_for_delivery method).

        """
        changed = False
        if new_datetime:
            changed = self._set_deliver_on(new_datetime)
        elif hours:
            changed = self._snooze_hours(hours)
        self.success = None
        self.expire_on = None
        if changed and save:
            self.save()
            # Fire a signal so we know this was snoozed.
            self.send_notification_snoozed()

    def _localize(self):
        """Ensure times are stored in UTC"""
        if self.deliver_on and self.deliver_on.tzinfo is None:
            self.deliver_on = pytz.utc.localize(self.deliver_on)
        if self.expire_on and self.expire_on.tzinfo is None:
            self.expire_on = pytz.utc.localize(self.expire_on)

    def send_notification_snoozed(self):
        notification_snoozed.send(
            sender=self.__class__,
            message=self,
            user=self.user,
            related_object=self.content_object,
            deliver_on=self.deliver_on
        )

    def save(self, *args, **kwargs):
        self._localize()
        super(GCMMessage, self).save(*args, **kwargs)

    def _get_gcm_client(self):
        return GCMClient(api_key=GCM['API_KEY'])

    @property
    def registered_devices(self):
        """Return the active registration IDs associated with the user."""
        # Note: if the user has no devices, creating a GCMMessage through
        # the manager (GCMMessage.objects.create) will fail.
        devices = GCMDevice.objects.filter(is_active=True, user=self.user)
        return list(devices.values_list("registration_id", flat=True))

    def _checkin(self, obj):
        """NOTE: This alters notifications related to the goals app because
        I couldn't think of a better place to put this. For the morning/evening
        checkings, we want:

        - object_type = 'checking'
        - object_id = 1 for morning
        - object_id = 2 for evening

        Motivation for this: 1) we don't make the message content any larger,
        and 2) it's easy to implement in the app. The downside is that this
        logic is in the notifications app, when it really _should_ be part of
        the goals app.

        """
        if obj['object_type'] == 'goal' and obj['object_id'] is None:
            obj['object_type'] = 'checkin'
            if obj['title'] == DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE:
                obj['object_id'] = 1
            elif obj['title'] == DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE:
                obj['object_id'] = 2
        return obj

    @property
    def content(self):
        """The Bundled content that gets sent as the messages payload.

        NOTE: This payload has a limit of 4096 bytes.
        """
        object_type = None
        if self.content_type:  # If we have a content type, use it's name.
            object_type = self.content_type.name.lower()

        user_mapping_id = None
        if self.content_object and hasattr(self.content_object, "get_user_mapping"):
            user_mapping = self.content_object.get_user_mapping(self.user)
            user_mapping_id = user_mapping.id if user_mapping else None

        return self._checkin({
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "object_type": object_type,
            "object_id": self.object_id,
            "user_mapping_id": user_mapping_id,
        })

    @property
    def content_json(self):
        """JSON-encoded message payload; NOTE: has a limit of 4096 bytes."""
        return json.dumps(self.content)

    def send(self, collapse_key=None, delay_while_idle=False, time_to_live=None):
        """Deliver this message to Google Cloud Messaging.

        This method accepts the following options as keyword arguments; These
        are options available thru pushjack and are just passed along.

        * collapse_key: Omitted for messages with a payload (default), specify
            'collapse_key' for a 'send-to-sync' message.
        * delay_while_idle:  If True indicates that the message should not be
            sent until the device becomes active. (default is False)
        * time_to_live: Time to Live. Default is 4 weeks.

        """
        logging.info("Sending GCMMessage, id = %s", self.id)
        client = self._get_gcm_client()
        options = {
            'delay_while_idle': delay_while_idle,
            'time_to_live': time_to_live,
        }
        if collapse_key is not None:
            options['collapse_key'] = collapse_key
        resp = client.send(self.registered_devices, self.content_json, **options)
        self._save_response(resp)
        return resp

    def _set_expiration(self, days=7):
        """Set the date/time at which this message should be expired (i.e.
        deleted) from our database. We want to set an expiration for some point
        in the future, so that users can receive these messages, but then snooze
        them for some time.

        The script that does the deletion runs nightly.

        """
        if self.response_code == 200:
            # Expire at some point in the future.
            self.expire_on = timezone.now() + timedelta(days=days)
            self.success = True

    def _save_response(self, resp):
        """This method saves response data from GCM. This is mostly good for
        debugging message delivery, and this method will parse out that data
        and populate the following fields:

        * resposne_code
        * response_text
        * response_data
        * registration_ids

        """
        report_pattern = "Status Code: {0}\nReason: {1}\nURL: {2}\n----\n"
        report = ""
        # Save the http response info
        for r in resp.responses:  # Should only be 1 item.
            report += report_pattern.format(r.status_code, r.reason, r.url)
            self.response_code = r.status_code
        self.response_text = report

        # Save all the registration_ids that GCM thinks it delivered to
        rids = []
        for msg in resp.messages:  # this is a list of dicts
            rids.extend(msg.get("registration_ids", []))
        self.registration_ids = "\n".join(rids)

        # Save the whole chunk of response data
        self.response_data = resp.data

        self._set_expiration()
        self.save()

    # Use the Custom Manager for GCMMessage objects.
    objects = GCMMessageManager()
