import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from goals.models import Trigger, UserAction
from notifications.models import GCMDevice, GCMMessage
from notifications.settings import DEFAULTS
from utils.user_utils import to_localtime


logger = logging.getLogger("loggly_logs")
ERROR = True
WARNING = False


class SingleItemList(list):
    """that only allows one item"""
    def append(self, item):
        if item not in self:
            super().append(item)


class Command(BaseCommand):
    help = 'Creates notification Messages for users Actions & Behaviors'
    _log_messages = SingleItemList()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages_created = 0
        self._behavior_trigger = Trigger.objects.get_default_behavior_trigger()

    def _get_behavior_trigger_localtime(self, user):
        # We need to convert this into the user's local timezone.
        # To do that, we make it naive, then make it aware using the user's
        # timezone.
        t = self._behavior_trigger.next()
        t = to_localtime(t, user)
        return t

    def write_log(self):
        for msg, error in self._log_messages:
            if error:
                logger.error(msg)
                self.stderr.write(msg)
            else:
                logger.warning(msg)
                self.stdout.write(msg)

    def create_behavior_message(self, user):
        """Create a single notification for ALL of a user's selected Behaviors."""
        try:
            # create(self, user, title, message, deliver_on, obj=None)
            m = GCMMessage.objects.create(
                user,
                DEFAULTS['DEFAULT_TITLE'],
                DEFAULTS['DEFAULT_TEXT'],
                self._get_behavior_trigger_localtime(user)
            )
            if m is not None:
                self._messages_created += 1
        except GCMDevice.DoesNotExist:
            msg = "User {0} has not registered a Device".format(user)
            self._log_messages.append((msg, ERROR))

    def create_message(self, user, obj, title, message, delivery_date):
        if delivery_date is None:
            msg = "{0}-{1} has no trigger date".format(obj.__class__.__name__, obj.id)
            self._log_messages.append((msg, ERROR))
        else:
            try:
                if len(title) > 256:
                    title = "{0}...".format(title[:253])
                m = GCMMessage.objects.create(
                    user, title, message, delivery_date, obj
                )
                if m is not None:
                    self._messages_created += 1
            except GCMDevice.DoesNotExist:
                msg = "User {0} has not registered a Device".format(user)
                self._log_messages.append((msg, ERROR))

    def handle(self, *args, **options):
        # Make sure everything is ok before we run this.
        self.check()

        # Schedule notifications for Behaviors (1 per user) IFF the user has
        # selected any Behaviors.
        User = get_user_model()

        # Only those users with devices, who have not messages scheduled
        users = User.objects.filter(gcmdevice__isnull=False)

        # Those with UserBehaviors selected
        for user in users.filter(userbehavior__isnull=False).distinct():
            self.create_behavior_message(user)

        # Schedule upcoming notifications for UserAction's Custom Trigger
        for ua in UserAction.objects.all():
            user_trigger = ua.trigger
            if user_trigger:
                self.create_message(
                    ua.user,
                    ua.action,
                    ua.action.notification_title,
                    ua.action.notification_text,
                    user_trigger.next()  # Should always be in the user's timezone
                )

        # Finish with a confirmation message
        m = "Created {0} notification messages.".format(self._messages_created)
        self._log_messages.append((m, WARNING))
        self.write_log()
