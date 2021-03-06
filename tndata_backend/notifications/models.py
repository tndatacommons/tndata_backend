import json
import logging
import pytz

from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django.utils import timezone

from jsonfield import JSONField
from pushjack import APNSClient, APNSSandboxClient, GCMClient
from pushjack.exceptions import (
    APNSInvalidTokenError,
    GCMInvalidRegistrationError,
)

from badgify_api.serializers import BadgeSerializer
from goals.settings import (
    DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE
)
from redis_metrics import metric
from utils.slack import post_message

from . import queue
from . managers import GCMMessageManager
from . settings import GCM, APNS_CERT_PATH
from . signals import notification_snoozed


logger = logging.getLogger(__name__)


class GCMDevice(models.Model):
    """A User's registered device."""
    DEVICE_TYPE_OPTIONS = (
        ('android', 'Android'),
        ('ios', 'iOS'),
    )
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
    device_type = models.CharField(
        max_length=32,
        help_text="Type of device",
        default='android',
        choices=DEVICE_TYPE_OPTIONS
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', '-created_on', 'registration_id']
        unique_together = ("registration_id", "user", "device_id")
        verbose_name = "GCM Device"
        verbose_name_plural = "GCM Devices"
        get_latest_by = 'updated_on'

    def __str__(self):
        return self.device_name or self.registration_id


class GCMMessage(models.Model):
    """A Notification Message sent via GCM."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    PRIORITIES = (
        (LOW, 'Low Priority'),
        (MEDIUM, 'Medium Priority'),
        (HIGH, 'High Priority'),
    )

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
        default=dict,
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
    queue_id = models.CharField(max_length=128, default='', blank=True)
    priority = models.CharField(
        max_length=32,
        default=LOW,
        choices=PRIORITIES,
        db_index=True
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0} on {1}".format(self.title, self.deliver_on)

    class Meta:
        ordering = ['-success', 'deliver_on', 'priority', '-created_on']
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

    def _enqueue(self):
        """Handle enqueuing our messages for delivery when saved."""
        if self.queue_id:
            # If we already have a queue ID, we need to re-enqueue, so cancel
            # those prior jobs.
            queue.UserQueue(self).remove()
            queue.cancel(self.queue_id)

        # Add the message to the queue, and save it's job ID (if any)
        job = queue.enqueue(self)
        if job:
            self.queue_id = job.id

    def send_notification_snoozed(self):
        notification_snoozed.send(
            sender=self.__class__,
            message=self,
            user=self.user,
            related_object=self.content_object,
            deliver_on=self.deliver_on
        )

    def save(self, *args, **kwargs):
        # Note: we need to save this so we have FK associates before we
        # can enqueue it into rq.
        if self.id is None:
            super(GCMMessage, self).save(*args, **kwargs)

        self._localize()
        if not self.success:  # Don't re-enqueue successfully sent messages
            self._enqueue()

        super(GCMMessage, self).save(*args, **kwargs)

    def _get_gcm_client(self, recipient_type=None):
        if recipient_type == "ios":
            try:
                key = GCM['IOS_API_KEY']
                assert key is not None
                return GCMClient(api_key=key)
            except (KeyError, AssertionError):
                raise ImproperlyConfigured(
                    "The IOS_API_KEY must be defined in order to deliver "
                    "push notifications to iOS devices"
                )
        return GCMClient(api_key=GCM['API_KEY'])

    def _get_apns_client(self):
        options = {
            'certificate': APNS_CERT_PATH,
            'default_error_timeout': 10,
            'default_expiration_offset': 2592000,
            'default_batch_size': 100
        }
        if settings.DEBUG or settings.STAGING:
            return APNSSandboxClient(**options)
        return APNSClient(**options)

    @property
    def android_devices(self):
        """Return a list of Registration IDs for the user's android devices"""
        # Note: if the user has no devices, creating a GCMMessage through
        # the manager (GCMMessage.objects.create) will fail.
        devices = GCMDevice.objects.filter(user=self.user, device_type='android')
        return list(devices.values_list("registration_id", flat=True))

    @property
    def ios_devices(self):
        """Return a list of Registration IDs for the user's android devices"""
        # Note: if the user has no devices, creating a GCMMessage through
        # the manager (GCMMessage.objects.create) will fail.
        devices = GCMDevice.objects.filter(user=self.user, device_type='ios')
        return list(devices.values_list("registration_id", flat=True))

    # -------------------------------------------------------------------------
    # Payload methods.
    #
    # The following methods are used by the `content` & `content_json`
    # properties to include serialized payload data in a push notifications.
    #
    # Each accepts a dictionary argument which it may modify, and each returns
    # a possibly modified dict.
    #
    #   * _payload_badge
    #   * _payload_checkin
    #
    # -------------------------------------------------------------------------

    def _payload_badge(self, payload):
        """If this is an Award, lets include it's badge data with the payload."""
        # NOTE: the content_object should be an Award instance.
        serializer = BadgeSerializer(self.content_object.badge)
        payload['badge'] = serializer.data
        return payload

    def _payload_checkin(self, payload):
        """This method alters the notification payload for the morning/evening
        check-ins. It adds the following data:

        - object_type = 'checkin'
        - object_id = 1 for morning
        - object_id = 2 for evening

        Motivation for this: 1) we don't make the message content any larger,
        and 2) it's easy to implement in the app. The downside is that this
        logic is in the notifications app, when it really _should_ be part of
        the goals app.

        """
        payload['object_type'] = 'checkin'
        if payload['title'] == DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE:
            payload['object_id'] = 1
        elif payload['title'] == DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE:
            payload['object_id'] = 2
        return payload

    @property
    def content(self):
        """The Bundled content that gets sent as the messages payload.

        NOTE: According to GCM, the payload has a limit of 4096 bytes, while
        for APNS:

        > When using the HTTP/2 provider API, maximum payload size is 4096
        > bytes. Using the legacy binary interface, maximum payload size is
        > 2048 bytes.

        """
        payload = {
            "id": self.id,
            "to": self.user.id,
            "title": self.title,
            "message": self.message,
            "object_type": None,
            "object_id": self.object_id,
            "user_mapping_id": None,
            "production": not (settings.DEBUG or settings.STAGING),
        }

        # If we have a content type, use it's name as the `object_type`
        if self.content_type:
            ct_name = self.content_type.name.lower().replace(' ', '')
            payload['object_type'] = ct_name

        # See if we've got a user-mapping ID (e.g. the UserAction.id)
        has_get_user_mapping = hasattr(self.content_object, "get_user_mapping")
        if self.content_object and has_get_user_mapping:
            user_mapping = self.content_object.get_user_mapping(self.user)
            try:
                payload['user_mapping_id'] = user_mapping.id
            except AttributeError:  # returned value was int or None-type
                payload['user_mapping_id'] = user_mapping

        # Include serialzed/extra data if appropriate.
        if payload['object_type'] == 'goal' and payload['object_id'] is None:
            payload = self._payload_checkin(payload)
        elif payload['object_type'] == 'award' and self.content_object:
            payload = self._payload_badge(payload)
        return payload

    @property
    def content_json(self):
        """JSON-encoded message payload; NOTE: has a limit of 4096 bytes."""
        from goals.encoder import JSONEncoder
        if not hasattr(self, "_content_json"):
            self._content_json = json.dumps(self.content, cls=JSONEncoder)
        return self._content_json

    @property
    def payload_size(self):
        return len(self.content_json)

    def _send_to_android_devices(self, android_ids, options):
        """Send push notifications to anddroid devices using GCM"""
        try:
            client = self._get_gcm_client(recipient_type='android')
            resp = client.send(android_ids, self.content_json, **options)
            self._handle_gcm_response(resp, request_type='android')
            self._remove_invalid_gcm_devices(resp.errors)  # handle old IDs
        except Exception as e:
            logging.error("[GCM] Notification Failure: %s", str(e))

    def _send_to_ios_devices(self, ios_ids, options):
        try:
            # ... Via GCM
            # options['low_priority'] = False  # always use priority=high for ios
            # client = self._get_gcm_client(recipient_type='ios')
            # resp = client.send(ios_ids, self.content_json, **options)
            # self._handle_gcm_response(resp, request_type='ios')
            # self._remove_invalid_gcm_devices(resp.errors)  # handle old IDs

            # ... Via APNS
            client = self._get_apns_client()
            payload = self.content  # send as extra, w/o title or message
            resp = client.send(
                ios_ids,
                payload.pop('message', ''),
                title=payload.pop('title', ''),
                # content_available=True,
                # title='Title',
                # title_loc_key='t_loc_key',
                # title_loc_args='t_loc_args',
                # action_loc_key='a_loc_key',
                # loc_key='loc_key',
                # launch_image='path/to/image.jpg',
                extra=payload
            )
            self._handle_apns_response(resp)
            self._remove_invalid_apns_devices(client.get_expired_tokens())
            client.close()
        except APNSInvalidTokenError:
            err_msg = "[APNS] removing device with APNS Token for message=%s"
            logging.warning(err_msg, str(self.id))
            # NOTE: I have no way to know which of the ios tokens caused this,
            # so I can either delete them all, delete none, or delete one.
            # I'm doing the former (delete 1 at a time), since I assume most
            # people will have 1 device, and for everyone else, we'll eventually
            # remove the invalid token.
            if len(ios_ids) > 0:
                GCMDevice.objects.filter(registration_id=ios_ids[0]).delete()
                post_message("#tech", err_msg % self.id)

        except Exception as e:
            logging.error("[APNS] Notification Failure: %s", str(e))

    def send(self, collapse_key=None, delay_while_idle=False, time_to_live=None):
        """Deliver this message to Google Cloud Messaging (both iOS & Android).

        This method accepts the following options as keyword arguments; These
        are options available thru pushjack and are just passed along.

        * collapse_key: Omitted for messages with a payload (default), specify
            'collapse_key' for a 'send-to-sync' message.
        * delay_while_idle:  If True indicates that the message should not be
            sent until the device becomes active. (default is False)
        * time_to_live: Time to Live. Default is 4 weeks.

        """
        logging.info("Sending GCMMessage, id = %s", self.id)
        options = {
            'delay_while_idle': delay_while_idle,
            'time_to_live': time_to_live,
            'low_priority': True,
        }
        if collapse_key is not None:
            options['collapse_key'] = collapse_key

        # Send to Android devices (if any)
        android_ids = self.android_devices
        if len(android_ids):
            self._send_to_android_devices(android_ids, options)

        # Send to iOS devices (if any)
        ios_ids = self.ios_devices
        if len(ios_ids):
            self._send_to_ios_devices(ios_ids, options)

        self._set_expiration()  # Now set an expiration date, if applicable.
        self.save()  # the above methods change state, so we need to save.
        return True

    def _set_expiration(self, days=7):
        """Set the date/time at which this object should be expired (i.e.
        deleted) from our database. We want to set an expiration for some point
        in the future, so that users can receive these messages, but then snooze
        them for some time.

        The script that does the deletion runs nightly.

        """
        if self.success:
            # Expire at some point in the future.
            self.expire_on = timezone.now() + timedelta(days=days)
            metric('GCM Message Sent', category='Notifications')

    def _remove_invalid_apns_devices(self, tokens):
        """Remove the GCMDevices whose registration_id matches any of the
        given tokens (these are no longer valid)."""
        GCMDevice.objects.filter(registration_id__in=tokens).delete()

    def _remove_invalid_gcm_devices(self, errors):
        """Given a list of errors from GCM, look for any instances of
        `GCMInvalidRegistrationError`, and delete any matching `GCMDevice`
        objects.

        * errors = a list of errors (if any)

        XXX: This is a destructive operation.

        """
        identifiers = [
            error.identifier for error in errors
            if isinstance(error, GCMInvalidRegistrationError) and error.identifier
        ]
        if len(identifiers) > 0:  # Don't hit the DB if we don't have to.
            GCMDevice.objects.filter(registration_id__in=identifiers).delete()

    def _handle_apns_response(self, resp):
        # Save all the tokens to which APNS delivered
        self.registration_ids += "\n".join(resp.tokens)

        if isinstance(self.response_data, list):
            self.response_data = {'apns': resp.token_errors}
        else:
            # Save the whole chunk of response data
            self.response_data['apns'] = resp.token_errors

        # Inspect the response data for a failure message; response data
        # may look like this, and may have both failures and successes.
        # If we have any success, consider this message succesfully sent
        if any(resp.successes):
            self.success = True
        elif any(resp.failures):
            self.success = False

        if any(resp.errors):
            for err in resp.errors:
                msg = "Code: {}\nDescription: {}\nIdentifier: {}\n----\n"
                self.response_text += msg.format(
                    err.code,
                    err.description,
                    err.identifier
                )

    def _handle_gcm_response(self, resp, request_type='android'):
        """This method handles the http response & data from GCM (after sending
        a message). There are a few things that can happen, here:

        The Response content is parsed, and the following fields are populated:

            * response_code
            * response_text
            * response_data
            * registration_ids

        """
        # Update the http response info from GCM
        report_pattern = "Status Code: {0}\nReason: {1}\nURL: {2}\n----\n"
        for r in resp.responses:  # Should only be 1 item.
            self.response_text += report_pattern.format(
                r.status_code,
                r.reason,
                r.url
            )
            self.response_code = r.status_code  # NOTE: not really accurage :/

        # Save all the registration_ids that GCM thinks it delivered to
        rids = set([rid for rid in self.registration_ids.split("\n") if rid])
        for msg in resp.messages:  # this is a list of dicts
            for rid in msg.get('registration_ids', []):
                rids.add(rid)
        self.registration_ids = "\n".join(rids)

        # Argh. I changed how we save things in `response_data`, but it's
        # possible that may be an existing list instead of a dict. If so,
        # i need to update the original data:
        if isinstance(self.response_data, list):
            self.response_data = {request_type: self.response_data}
        else:
            # Save the whole chunk of response data
            self.response_data[request_type] = resp.data

        # Inspect the response data for a failure message; response data
        # may look like this, and may have both failures and successes.
        #
        # [ {'canonical_ids': 0,
        #    'failure': 1,
        #    'multicast_id': 6059042386405224298,
        #    'results': [{'error': 'NotRegistered'}],
        #    'success': 0}]
        #
        # If we have any success, consider this message succesfully sent
        successes = [d.get('success', False) for d in resp.data]
        failures = [d.get('failure', False) for d in resp.data]
        if any(successes):
            self.success = True
        elif any(failures):
            self.success = False

        # If we failed set the response text
        if not self.success:
            msg = ""
            for item in resp.data:
                for result in item.get('results', []):
                    if 'error' in result:
                        msg += result['error'] + "\n"
            self.response_text += "{}\n----\n".format(msg)

    def get_daily_message_limit(self):
        try:
            return self.user.userprofile.maximum_daily_notifications
        except (models.ObjectDoesNotExist, AttributeError, ValueError):
            return 20

    # Use the Custom Manager for GCMMessage objects.
    objects = GCMMessageManager()


@receiver(pre_delete, sender=GCMMessage, dispatch_uid="remove-message-from-queue")
def remove_message_from_queue(sender, instance, *args, **kwargs):
    """Prior to deleting a GCMMessage, remove its corresponding task from
    the work queue/scheduler.

    """
    queue.UserQueue(instance).remove()  # Remove it from the queue
    queue.cancel(instance.queue_id)  # Cancel the scheduled Job
