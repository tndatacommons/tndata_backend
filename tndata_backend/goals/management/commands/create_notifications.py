import logging
import pytz

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from goals.models import Trigger, UserAction
from notifications.models import GCMDevice, GCMMessage
from notifications.settings import DEFAULTS
from utils import slack


logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Creates notification Messages for users Actions & Behaviors'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages_created = 0
        self._behavior_trigger = Trigger.objects.get_default_behavior_trigger()

    def _to_localtime(self, t, user):
        """given a time, convert it to the user's localtime."""
        if user.userprofile.timezone:
            tz = pytz.timezone(user.userprofile.timezone)
            t = timezone.make_naive(t)
            t = timezone.make_aware(t, timezone=tz)
        return t

    def _get_behavior_trigger_localtime(self, user):
        # We need to convert this into the user's local timezone.
        # To do that, we make it naive, then make it aware using the user's
        # timezone.
        t = self._behavior_trigger.next()
        t = self._to_localtime(t, user)
        return t

    def create_behavior_message(self, user):
        """Create a single notification for ALL of a user's selected Behaviors."""
        # TODO: Give users a way to specify a single, priority (behavior)
        # custom reminder instead of using the default.
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
                slack.log_message(m, "Behavior Message Created")
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
                    slack.log_message(m, "Message Created")
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

        # Schedule notifications for UserAction's Custom Trigger
        for ua in UserAction.objects.with_custom_triggers():
            self.create_message(
                ua.user,
                ua.action,
                ua.action.notification_title,
                ua.action.notification_text,
                ua.custom_trigger.next()
            )

        # Schedule notifications for UserAction's with just the default trigger
        for ua in UserAction.objects.with_only_default_triggers():
            self.create_message(
                ua.user,
                ua.action,
                ua.action.notification_title,
                ua.action.notification_text,
                self._to_localtime(ua.action.default_trigger.next(), ua.user)
            )

        # Finish with a confirmation message
        m = "Created {0} notification messages.".format(self._messages_created)
        logger.info(m)
        self.stdout.write(m)
