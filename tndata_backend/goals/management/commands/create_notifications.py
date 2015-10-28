import logging

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

import waffle

from goals.models import Goal, Trigger, UserAction
from goals.settings import (
    DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_MORNING_GOAL_NOTIFICATION_TEXT,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TEXT,
)
from notifications.models import GCMDevice, GCMMessage
from utils.user_utils import to_utc

logger = logging.getLogger("loggly_logs")
ERROR = True
WARNING = False


class SingleItemList(list):
    """that only allows one item"""
    def append(self, item):
        if item not in self:
            super().append(item)


class Command(BaseCommand):
    help = 'Generates GCM notification messages for users.'
    _log_messages = SingleItemList()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages_created = 0

    def write_log(self):
        for msg, error in self._log_messages:
            if error:
                logger.error(msg)
                self.stderr.write(msg)
            else:
                logger.warning(msg)
                self.stdout.write(msg)

    def create_message(self, user, obj, title, message, delivery_date):

        # kwargs to GCMMessage.objects.create
        kwargs = {'obj': None, 'content_type': None}

        # obj can be None, a model instance, or a ContentType
        if isinstance(obj, ContentType):
            kwargs['content_type'] = obj
        else:
            kwargs['obj'] = obj

        if delivery_date is None:
            msg = "{0}-{1} has no trigger date".format(obj.__class__.__name__, obj.id)
            self._log_messages.append((msg, ERROR))
        else:
            try:
                if len(title) > 256:
                    title = "{0}...".format(title[:253])

                args = (user, title, message, delivery_date)
                m = GCMMessage.objects.create(*args, **kwargs)

                if m is not None:
                    self._messages_created += 1
            except GCMDevice.DoesNotExist:
                msg = "User {0} has not registered a Device".format(user)
                self._log_messages.append((msg, ERROR))

    def schedule_action_notifications(self):
        # Schedule upcoming notifications for all UserActions with:
        # - published Actions (whose parent behavior is also published)
        # - users that have a GCMDevice registered
        useractions = UserAction.objects.filter(
            action__state='published',
            action__behavior__state='published',
            user__gcmdevice__isnull=False
        )
        for ua in useractions.distinct():
            user_trigger = ua.trigger
            if user_trigger:
                # Will be in the user's timezone
                deliver_on = user_trigger.next(user=ua.user)
                deliver_on = to_utc(deliver_on)

                self.create_message(
                    ua.user,
                    ua.action,
                    ua.action.notification_title,
                    ua.action.notification_text,
                    deliver_on,
                )

    def schedule_morning_goal_notifications(self, users):
        trigger = Trigger.objects.get_default_morning_goal_trigger()
        for user in users:
            # Convert trigger to the user's timezone
            deliver_on = trigger.next(user=user)
            deliver_on = to_utc(deliver_on)

            self.create_message(
                user,
                ContentType.objects.get_for_model(Goal),
                DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
                DEFAULT_MORNING_GOAL_NOTIFICATION_TEXT,
                deliver_on
            )

    def schedule_evening_goal_notifications(self, users):
        trigger = Trigger.objects.get_default_evening_goal_trigger()
        for user in users:
            # Convert trigger to the user's timezone
            deliver_on = trigger.next(user=user)
            deliver_on = to_utc(deliver_on)

            self.create_message(
                user,
                ContentType.objects.get_for_model(Goal),
                DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE,
                DEFAULT_EVENING_GOAL_NOTIFICATION_TEXT,
                deliver_on
            )

    def handle(self, *args, **options):
        # Make sure everything is ok before we run this.
        self.check()
        self.schedule_action_notifications()

        User = get_user_model()
        users = User.objects.filter(gcmdevice__isnull=False).distinct()

        if waffle.switch_is_active('goals-morning-checkin'):
            self.schedule_morning_goal_notifications(users)
        if waffle.switch_is_active('goals-evening-checkin'):
            self.schedule_evening_goal_notifications(users)

        # Finish with a confirmation message
        m = "Created {0} notifications.".format(self._messages_created)
        self._log_messages.append((m, WARNING))
        self.write_log()
