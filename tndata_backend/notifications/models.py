from datetime import datetime
from hashlib import md5

from django.conf import settings
from django.db import models

from jsonfield import JSONField
from pushjack import GCMClient

from . settings import GCM


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
        help_text="Unique ID for this message."
    )

    # TODO: separate the bits of the message into separate fields.
    # e.g. title, message, object_type (e.g. behavior), object_id, then create
    # a `content` property that returns a dict/json
    content = JSONField(help_text="JSON content for the message")

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
        help_text="Date/Time on which the message should be delivered"
    )
    expire_on = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date/Time on which this message should expire (be deleted)"
    )
    created_on = models.DateTimeField(auto_now_add=True)

    # TODO: the recurring info is stored in goals.Triggers; We need some way
    # for that app to create these notifications.
    #
    # TODO: associate with a goals model via a Generic Relation?
    # https://docs.djangoproject.com/en/1.8/ref/contrib/contenttypes/
    #
    # TODO: management command to remove successfully sent (& expired) messages

    def __str__(self):
        return self.message_id

    class Meta:
        ordering = ['deliver_on']
        unique_together = ("user", "message_id")
        verbose_name = "GCM Message"
        verbose_name_plural = "GCM Messages"

    def _set_message_id(self):
        """Sets the message id to what should be something unique."""
        d = datetime.utcnow().strftime("%c").encode("utf8")
        self.message_id = md5(d).hexdigest()

    def save(self, *args, **kwargs):
        if not self.message_id:
            self._set_message_id()
        super(GCMMessage, self).save(*args, **kwargs)

    def _get_gcm_client(self):
        return GCMClient(api_key=GCM['API_KEY'])

    @property
    def registration_ids(self):
        """Return the active registration IDs associated with the user."""
        devices = GCMDevice.objects.filter(is_active=True, user=self.user)
        return list(devices.values_list("registration_id", flat=True))

    def send(self, collapse_key=None, delay_while_idle=True, ttl=None):
        """Deliver this message to Google Cloud Messaging.

        * collapse_key: Omitted for messages with a payload (default), specify
            'collapse_key' for a 'send-to-sync' message.
        * delay_while_idle:  If True indicates that the message should not be
            sent until the device becomes active. (default is True)
        * ttl: Time to Live. Default is 4 weeks.

        """
        client = self._get_gcm_client()
        options = {
            'delay_while_idle': delay_while_idle,
            'time_to_live': ttl,
        }
        if collapse_key is not None:
            options['collapse_key'] = collapse_key
        resp = client.send(self.registration_ids, self.content, **options)
        self._save_response(resp)
        return resp

    def _save_response(self, resp):
        report_pattern = "Status Code: {0}\nReason: {1}\nURL: {2}\n----\n"
        report = ""
        for r in resp.responses:
            report += report_pattern.format(r.status_code, r.reason, r.url)
        self.response_text = report
        self.save()
