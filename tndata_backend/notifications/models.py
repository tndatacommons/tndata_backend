import json
import logging
import pytz

from datetime import datetime
from hashlib import md5

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from pushjack import GCMClient
from . managers import GCMMessageManager
from . settings import GCM


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
        ordering = ['user', 'registration_id']
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
    message_id = models.CharField(
        max_length=32,
        db_index=True,
        blank=True,  # Generated automatcially
        help_text="Unique ID for this message."
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
        return self.message_id

    class Meta:
        ordering = ['deliver_on']
        unique_together = ("user", "message_id")
        verbose_name = "GCM Message"
        verbose_name_plural = "GCM Messages"

    def _set_message_id(self):
        """This is an attempt to ensure we don't send duplicate messages to
        a user. This hashes the content type & content object's ID (if available)
        (which should always have consistent title/messages) with the user.

        If there's no related content object, this will hash the current
        date & time for the message id.

        """
        content_info = datetime.utcnow().strftime("%c")
        if self.content_object:
            # If we have additional content, use taht as well.
            content_info = "{0}-{1}-{2}-{3}".format(
                content_info,
                self.content_type.name,
                self.object_id,
                self.user.id
            )
        self.message_id = md5(content_info.encode("utf8")).hexdigest()

    def _localize(self):
        """Ensure times are stored in UTC"""
        if self.deliver_on and self.deliver_on.tzinfo is None:
            self.deliver_on = pytz.utc.localize(self.deliver_on)
        if self.expire_on and self.expire_on.tzinfo is None:
            self.expire_on = pytz.utc.localize(self.expire_on)

    def save(self, *args, **kwargs):
        self._localize()
        if not self.message_id:
            self._set_message_id()
        super(GCMMessage, self).save(*args, **kwargs)

    def _get_gcm_client(self):
        return GCMClient(api_key=GCM['API_KEY'])

    @property
    def registration_ids(self):
        """Return the active registration IDs associated with the user."""
        # Note: if the user has no devices, creating a GCMMessage through
        # the manager (GCMMessage.objects.create) will fail.
        devices = GCMDevice.objects.filter(is_active=True, user=self.user)
        return list(devices.values_list("registration_id", flat=True))

    @property
    def content(self):
        """The Bundled content that gets sent as the messages payload.

        NOTE: This payload has a limit of 4096 bytes.
        """
        object_type = None
        object_id = None
        if self.content_type and self.object_id:
            object_type = self.content_type.name.lower()
            object_id = self.object_id

        return {
            "title": self.title,
            "message": self.message,
            "object_type": object_type,  # What if None?
            "object_id": object_id,
        }

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
        resp = client.send(self.registration_ids, self.content_json, **options)
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
        report_pattern = "Status Code: {0}\nReason: {1}\nURL: {2}\n----\n"
        report = ""
        for r in resp.responses:  # Should only be 1 item.
            report += report_pattern.format(r.status_code, r.reason, r.url)
            self.response_code = r.status_code
        self.response_text = report

        self._set_expiration()
        self.save()

    # Use the Custom Manager for GCMMessage objects.
    objects = GCMMessageManager()
