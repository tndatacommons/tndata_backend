from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from .managers import ChatMessageManager


class ChatMessage(models.Model):
    """A persisted chat message."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)  # Message author.
    # XXX: Right now, rooms are of the form `chat-<userid>-<userid>`, and we
    # can look up recipients that way, but that's not gonna be the case for
    # group rooms....
    #
    # We need some way to save the message recipient.
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


class ChatGroup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)  # Group "owner"
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="chatgroup_member"
    )
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Chat Group"
        verbose_name_plural = "Chat Group"

    @property
    def members_count(self):
        return self.members.all().count()

    def get_absolute_url(self):
        return reverse("chat:group-chat", args=[self.pk, self.slug])
