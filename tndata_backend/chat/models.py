import logging

from django.conf import settings
from django.db import models
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def generate_room_name(values):
    """Given an iterable of values that can either be strings or User objects,
    generate a room name."""

    values = [v.username if hasattr(v, 'username') else v for v in values]
    values = sorted(values)
    return slugify("chat-{}-{}".format(*values))


class ChatMessageManager(models.Manager):

    def unread(self):
        """Return a queryset of unread chat messages."""
        return self.get_queryset().filter(read=False)

    def to_user(self, user):
        """Return a queryset of messages that were sent to the given user.

        NOTE: Since we only save the user that created the message, this
        filters are the room name, which includes both users' usernames.
        """
        results = self.get_queryset().filter(room__icontains=user.username)
        results = results.exclude(user=user)  # remove messages the user authored
        return results

    def for_users(self, users):
        """Given a pair of users, return the ChatMessages for their chat room."""
        room_name = generate_room_name(users)
        return self.get_queryset().filter(room=room_name)


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

    objects = ChatMessageManager()
