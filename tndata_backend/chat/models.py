import logging

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class ChatMessage(models.Model):
    """A persisted chat message."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    room = models.CharField(max_length=256, default="")
    text = models.TextField(default="")
    read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
