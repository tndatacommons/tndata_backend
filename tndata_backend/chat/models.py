from django.conf import settings
from django.db import models

from .managers import ChatMessageManager


class ChatMessage(models.Model):
    """A persisted chat message."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    room = models.CharField(max_length=256, default="", db_index=True)
    text = models.TextField(default="")
    read = models.BooleanField(default=False)

    # NOTE: This is an md5 digest of the message's author + text + creation time.
    # It's used as an intial ID for the message, which we need to know prior
    # to the object's creation time (for read receipts)
    digest = models.CharField(max_length=32, blank=True, default='', db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    objects = ChatMessageManager()


# -----------------------------------------------------------------------------
# TODO: IDEAS for group messaging.
# -----------------------------------------------------------------------------
#
# 1. Create a `Group` model (auto-do this for each Course?) & auto-subscribe
#    the relevant people? We could create messages here without moving them
#    through the websocket?
# 2. We could craete a websocket channel for some auto-generated group name?
# 3. How to make it single-User -> Group, not a free-for-all chat?
# 4. Broadcast messages is what we're after.
