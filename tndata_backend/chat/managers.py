from datetime import timedelta

from django.db import models
from django.utils import timezone

from .utils import generate_room_name


class ChatMessageManager(models.Manager):

    def unread(self):
        """Return a queryset of unread chat messages."""
        return self.get_queryset().filter(read=False)

    def to_user(self, user):
        """Return a queryset of messages that were sent to the given user.

        NOTE: Since we only save the user that created the message, this
        filters are the room name, which includes both users' IDs.
        """
        results = self.get_queryset().filter(room__icontains=user.id)
        results = results.exclude(user=user)  # remove messages the user authored
        return results

    def for_users(self, users):
        """Given a pair of users, return the ChatMessages for their chat room."""
        room_name = generate_room_name(users)
        return self.get_queryset().filter(room=room_name)

    def recent(self, since=15):
        """Return a queryset of *recent* ChatMessage objects.

        The times for which items are considered recent include:

        - since: Age of a message in minues. By default, this will include
          messages that were created within the past 15 minutes.

        """
        since = timezone.now() - timedelta(minutes=since)
        queryset = self.get_queryset()
        return queryset.filter(created_on__gt=since)
