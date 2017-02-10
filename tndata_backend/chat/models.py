from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .managers import ChatMessageManager


class ChatMessage(models.Model):
    """A persisted chat message."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="Message sender"
    )
    # -------------------------------------------------------------------------
    # XXX: Right now, rooms are of the form `chat-<userid>-<userid>`, and we
    # can look up recipients that way, but that's not gonna be the case for
    # group rooms....
    #
    # We need some way to save the message recipient.
    # IDEA: recipients: a list of user-id's to which the message should have
    #       gone. We need to be able to look up messages for recipients more accurately
    # OR: a M2M field for recipeints.
    #
    #       user.chat_messages.unread()   # ideal.
    #
    # -------------------------------------------------------------------------
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='chatmessages_received',
        help_text='Message recipient(s)'
    )
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


@receiver(post_save, sender=ChatMessage, dispatch_uid='set-chatmessage-recipients')
def set_chatmessage_recipients(sender, instance, created, **kwargs):
    """After a message is saved, we try to set the Users who would have been
    the message's recipients. This is not done in the websocket consumer,
    because we don't have all the recipient info available.

    Here's the strategy:

    1. Person-to-person messages have a chat room of the form `chat-<id>-<id>`.
       If that's the kind of message we get, we'll look up those users.
    2. TODO: Otherwise, we'll pull all the messages from the related Chat Group

    """
    User = get_user_model()

    if instance and instance.room.startswith("chat-"):
        ids = instance.room[len("chat-"):].split('-')
        users = User.objects.filter(pk__in=ids)
        users = users.exclude(pk=instance.user.id)
        for user in users:
            instance.recipients.add(user)

    # TODO: do this for groups.


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
