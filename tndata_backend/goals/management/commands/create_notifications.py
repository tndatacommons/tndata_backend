import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from goals.models import Trigger, UserAction
from notifications.models import GCMDevice, GCMMessage
from notifications.settings import DEFAULTS


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates notification Messages for users Actions & Behaviors'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages_created = 0
        self._behavior_trigger = Trigger.objects.get_default_behavior_trigger()

    def create_behavior_message(self, user):
        """We create a single notification for ALL of a user's selected Behaviors."""

        # TODO: Give users a way to specify a single, priority (behavior)
        # custom reminder instead of using the default.
        try:
            # create(self, user, title, message, deliver_on, obj=None)
            m = GCMMessage.objects.create(
                user,
                DEFAULTS['DEFAULT_TITLE'],
                DEFAULTS['DEFAULT_TEXT'],
                self._behavior_trigger.next(),
            )
            if m is not None:
                self._messages_created += 1
            else:
                msg = "Failed to create Behavior Message for {0}".format(user)
                logger.warning(msg)
                self.stderr.write(msg)
        except GCMDevice.DoesNotExist:
            msg = "User {0} has not registered a Device".format(user)
            logger.error(msg, exc_info=1)
            self.stderr.write(msg)

    def create_message(self, user, obj, title, message, delivery_date):
        if delivery_date is None:
            msg = "{0}-{1} has no trigger date".format(obj.__class__.__name__, obj.id)
            logger.error(msg)
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
                    logger.warning(msg)
                    self.stderr.write(msg)
            except GCMDevice.DoesNotExist:
                msg = "User {0} has not registered a Device".format(user)
                logger.error(msg, exc_info=1)
                self.stderr.write(msg)

    def handle(self, *args, **options):
        # Make sure everything is ok before we run this.
        self.check()

        # Schedule notifications for Behaviors (1 per user) IFF the user has
        # selected any Behaviors.
        User = get_user_model()
        for user in User.objects.filter(userbehavior__isnull=False).distinct():
            self.create_behavior_message(user)

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
        logger.info(m)
        self.stdout.write(m)
