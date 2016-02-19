from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

import waffle

from goals.models import CustomAction, Goal, Trigger, UserAction
from goals.settings import (
    DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_MORNING_GOAL_NOTIFICATION_TEXT,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TEXT,
)
from notifications.models import GCMDevice, GCMMessage
from utils.user_utils import to_utc

import logging

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

    def create_message(self, user, obj, title, message, delivery_date, priority=None):

        if delivery_date is None:
            msg = "{0}-{1} has no trigger date".format(obj.__class__.__name__, obj.id)
            self._log_messages.append((msg, ERROR))
            return None

        # Only create messages that should be delivered within the next 24 hours
        now = timezone.now()
        threshold = timezone.now() + timedelta(hours=24)
        if delivery_date and delivery_date < now or delivery_date > threshold:
            msg = "{0}-{1} delivery date not within 24 hours".format(obj.__class__.__name__, obj.id)
            self._log_messages.append((msg, ERROR))
            return None  # The message is either too old or to far out.

        # XXX: If we're running in Staging / Dev environments, restrict
        # notifications to our internal users.
        staging_or_dev = (settings.STAGING or settings.DEBUG)
        if staging_or_dev and not user.email.endswith('@tndata.org'):
            return None

        # kwargs to GCMMessage.objects.create
        # TODO: How to decide on message priority, if it's not already set?
        kwargs = {'obj': None, 'content_type': None, 'priority': priority}

        # obj can be None, a model instance, or a ContentType
        if isinstance(obj, ContentType):
            kwargs['content_type'] = obj
        else:
            kwargs['obj'] = obj

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

    def schedule_customaction_notifications(self):
        # Schedule upcoming notifications for all CustomActions for users with:
        # - users that have a GCMDevice registered
        # - TODO: custom actions that have some text
        customactions = CustomAction.objects.filter(
            user__gcmdevice__isnull=False
        )

        for a in customactions.distinct():
            if a.trigger:
                # Will be in the user's timezone
                deliver_on = a.trigger.next(user=a.user)
                deliver_on = to_utc(deliver_on)

                self.create_message(
                    a.user,
                    a,
                    a.customgoal.title,
                    a.notification_text,
                    deliver_on,
                    priority=GCMMessage.MEDIUM
                )

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
                    ua.get_notification_title(),
                    ua.get_notification_text(),
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
        if waffle.switch_is_active('goals-customactions'):
            self.schedule_customaction_notifications()

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
