from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from random import randint

from goals.models import UserAction
from notifications.models import GCMDevice, GCMMessage
from notifications.settings import DEFAULTS


class Command(BaseCommand):
    help = 'Creates notification Messages for users Actions & Behaviors'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages_created = 0

    def create_behavior_message(self, user, delivery_date=None):
        """We create a single notification for ALL of a user's selected Behaviors."""
        if delivery_date is None:
            delivery_date = datetime.utcnow() + timedelta(hours=randint(3, 6))

        try:
            m = GCMMessage.objects.create(
                user,
                DEFAULTS['DEFAULT_TITLE'],
                DEFAULTS['DEFAULT_TEXT'],
                delivery_date
            )
            if m is not None:
                self._messages_created += 1
            else:
                msg = "Failed to create Behavior Message for {0}".format(user)
                self.stderr.write(msg)
        except GCMDevice.DoesNotExist:
            msg = "User {0} has not registered a Device".format(user)
            self.stderr.write(msg)

    def create_message(self, user, obj, title, message, delivery_date):
        if delivery_date is None:
            msg = "{0}-{1} has no trigger date".format(obj.__class__.__name__, obj.id)
            self.stderr.write(msg)
        else:
            try:
                if len(title) > 256:
                    title = "{0}...".format(title[:253])
                m = GCMMessage.objects.create(
                    user, title, message, delivery_date, obj
                )
                if m is not None:
                    self._messages_created += 1
                else:
                    msg = "Failed to create message for {0}/{1}-{2}".format(
                        user, obj.__class__.__name__, obj.id
                    )
                    self.stderr.write(msg)
            except GCMDevice.DoesNotExist:
                msg = "User {0} has not registered a Device".format(user)
                self.stderr.write(msg)

    def handle(self, *args, **options):
        # Make sure everything is ok before we run this.
        self.check()

        # Schedule notifications for Behaviors (1 per user)
        User = get_user_model()
        for user in User.objects.filter(userbehavior__isnull=False).distinct():
            self.create_behavior_message(user)  # TODO: which trigger/date?

        # Schedule notifications for Actions
        for ua in UserAction.objects.all():
            self.create_message(
                ua.user,
                ua.action,
                ua.action.notification_title,
                ua.action.notification_text,
                ua.action.get_trigger().next()
            )

        # Finish with a confirmation message
        m = "Created {0} notification messages.".format(self._messages_created)
        self.stdout.write(m)
