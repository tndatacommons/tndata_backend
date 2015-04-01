import json
from datetime import datetime
from hashlib import md5

from django.conf import settings
from django.db import models

from jsonfield import JSONField
from pushjack import GCMClient, create_gcm_config

from . settings import GCM


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
    registration_id = models.CharField(
        max_length=256,
        db_index=True,
        help_text="The Android device ID"
    )
    content = JSONField(help_text="JSON content for the message")

    # Successful deliver? True/False, Null == message not sent.
    success = models.NullBooleanField(
        help_text="Whether or not the message was delivered successfully"
    )
    response_code = models.IntegerField(blank=True, null=True)
    response_text = models.CharField(max_length=256, blank=True)

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

    # TODO: Should a message be set as recurring, here?

    def __str__(self):
        return self.message_id

    class Meta:
        ordering = ['deliver_on']
        unique_together = ("registration_id", "message_id")
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

    def _get_gcm_config(self):
        return create_gcm_config({
            'GCM_API_KEY': GCM['API_KEY'],
            'GCM_URL': GCM['URL'],
            'GCM_MAX_RECIPIENTS': GCM['MAX_RECIPIENTS'],
        })

    def _get_gcm_client(self):
        return GCMClient(self._get_gcm_config())

    def send(self, collapse_key=None, delay_while_idle=True, ttl=2419200):
        """Deliver this message to Google Cloud Messaging.

        * collapse_key: Omitted for messages with a payload (default), specify
            'collapse_key' for a 'send-to-sync' message.
        * delay_while_idle: Default is True. When True, don't send if device is
            unavailable (e.g. turned off).
        * ttl: Default is 4 weeks. Lifetime of the message; it expires from GCM
            after this. Use 0 for now-or-never messages.

        """
        client = self._get_gcm_client()
        options = {
            'delay_while_idle': delay_while_idle,
            'ttl': ttl,
        }
        if collapse_key is not None:
            options['collapse_key'] = collapse_key
        result = client.send(self.registration_id, self.content, **options)
        # TODO: Inspect result to see if successful; update accordingly.
        return result

    def get_content_data(self):
        """return a parsed version of the Json `content`."""
        return json.loads(self.content)
