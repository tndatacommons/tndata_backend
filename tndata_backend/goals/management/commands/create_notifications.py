from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

import waffle

from goals.models import CustomAction, Goal, Trigger
from goals.sequence import get_next_useractions_in_sequence
from goals.settings import (
    DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_MORNING_GOAL_NOTIFICATION_TEXT,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE,
    DEFAULT_EVENING_GOAL_NOTIFICATION_TEXT,
)
from notifications.models import GCMDevice, GCMMessage
from utils.slack import post_private_message
from utils.user_utils import to_utc

import logging

logger = logging.getLogger(__name__)
ERROR = True
WARNING = False


class SingleItemList(list):
    """A list that only allows unique elements"""
    def append(self, item):
        if item not in self:
            super().append(item)


class Command(BaseCommand):
    help = 'Generates GCM notification messages for users.'
    _log_messages = SingleItemList()

    def __init__(self, *args, **kwargs):
        self._start_time = timezone.now()
        super().__init__(*args, **kwargs)
        self._messages_created = 0
        self._slack_messages = defaultdict(set)

    def _to_slack(self, user, message):
        """record a slack message to send to the given user."""
        self._slack_messages[user].add(message)

    def write_log(self):
        # Write our log messages.
        for msg, error in self._log_messages:
            if error:
                logger.error(msg)
                self.stderr.write(msg)
            else:
                logger.warning(msg)
                self.stdout.write(msg)

        # Then post our slack messages (if any)
        for user, message_set in self._slack_messages.items():
            for message in message_set:
                post_private_message(user, message)

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help=("Restrict this command to the given User. "
                  "Accepts a username, email, or id")
        )

    def _get_users(self, options):
        User = get_user_model()

        # Check to see if we're just running this for a specific user
        if options.get('user', False):
            user = options['user']
            try:
                if user.isnumeric():
                    criteria = Q(id=user)
                else:
                    criteria = (Q(username=user) | Q(email=user))
                # Return an iterable, but use .get() to raise an exception
                # if there's not matching user.
                user = User.objects.get(criteria)
                return [user]
            except User.DoesNotExist:
                raise CommandError("Could not find user: {0}".format(user))

        # Else: Find all the users that have GCM Devices.
        return User.objects.filter(gcmdevice__isnull=False).distinct()

    def create_message(self, user, obj, title, message, delivery_date,
                       priority=None, trigger=None):

        if delivery_date is None:
            msg = "{0}-{1} has no trigger date".format(obj.__class__.__name__, obj.id)
            self._log_messages.append((msg, ERROR))
            return None

        # XXX: If we're running in Staging / Dev environments, restrict
        # notifications to our internal users.
        staging_or_dev = (settings.STAGING or settings.DEBUG)
        if staging_or_dev and not user.email.endswith('@tndata.org'):
            return None

        # kwargs to GCMMessage.objects.create
        kwargs = {'obj': None, 'content_type': None, 'priority': priority}

        # Include the valid date range for dynamic triggers
        if trigger and trigger.is_dynamic:
            kwargs['valid_range'] = trigger.dynamic_range()

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
        customactions = CustomAction.objects.filter(
            user__gcmdevice__isnull=False
        )

        for customaction in customactions.distinct():
            if customaction.trigger:
                # Will be in the user's timezone
                deliver_on = customaction.trigger.next(user=customaction.user)
                deliver_on = to_utc(deliver_on)
                if deliver_on and deliver_on < self.threshold:
                    self.create_message(
                        customaction.user,
                        customaction,
                        customaction.customgoal.title,
                        customaction.notification_text,
                        deliver_on,
                        priority=customaction.priority
                    )

    def schedule_action_notifications(self, users):
        """Given a queryset of users, we first:

        1. Schedule all of their dynamic notifications, based on the item's
           Sequencing (e.g. items that have not been completed, ordered by their
           specified Goal/Behavior/Action sequence number)
        2. Schedule their non-dynamic (e.g. recurring) notifications.

        """
        for user in users:
            # Sequenced Goals, Behaviors, Actions
            for ua in get_next_useractions_in_sequence(user):
                # Retrive the `next_reminder`, which will be in the
                # user's timezone, and may have been created weeks or
                # months ago. This is slightlly differnt from other
                # UserActions, because we don't re-generate
                # these on the fly
                deliver_on = to_utc(ua.next_reminder)
                if deliver_on and deliver_on < self.threshold:
                    self.create_message(
                        user,
                        ua.action,
                        ua.get_notification_title(),
                        ua.get_notification_text(),
                        deliver_on,
                        priority=ua.priority,
                        trigger=ua.trigger
                    )

            # XXX; Very inefficient;
            # schedule the non-dynamic notifications.
            for ua in user.useraction_set.published().distinct():
                if ua.trigger and not ua.trigger.is_dynamic:
                    # Will be in the user's timezone
                    deliver_on = to_utc(ua.trigger.next(user=user))
                    if deliver_on and deliver_on < self.threshold:
                        self.create_message(
                            user,
                            ua.action,
                            ua.get_notification_title(),
                            ua.get_notification_text(),
                            deliver_on,
                            priority=ua.priority
                        )

    def schedule_morning_goal_notifications(self, users):
        trigger = Trigger.objects.get_default_morning_goal_trigger()
        for user in users:
            # Convert trigger to the user's timezone
            deliver_on = trigger.next(user=user)
            deliver_on = to_utc(deliver_on)

            if deliver_on and deliver_on < self.threshold:
                self.create_message(
                    user,
                    ContentType.objects.get_for_model(Goal),
                    DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
                    DEFAULT_MORNING_GOAL_NOTIFICATION_TEXT,
                    deliver_on,
                    priority=GCMMessage.LOW
                )

    def schedule_evening_goal_notifications(self, users):
        trigger = Trigger.objects.get_default_evening_goal_trigger()
        for user in users:
            # Convert trigger to the user's timezone
            deliver_on = trigger.next(user=user)
            deliver_on = to_utc(deliver_on)

            if deliver_on and deliver_on < self.threshold:
                self.create_message(
                    user,
                    ContentType.objects.get_for_model(Goal),
                    DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE,
                    DEFAULT_EVENING_GOAL_NOTIFICATION_TEXT,
                    deliver_on,
                    priority=GCMMessage.LOW
                )

    def handle(self, *args, **options):
        # ---------------------------------------------------------------------
        # XXX: Don't create notifications that are too far in the future
        # Attempting to do this has always been a little tricky, and we disabled
        # this for a while, but we're getting too many messages queued up.
        #
        # We also recently disabled the monthly option, so this should be safe.
        #
        self.threshold = timezone.now() + timedelta(days=30)
        # ---------------------------------------------------------------------

        # This switch allows us to completely disable creation of notifications
        if not waffle.switch_is_active('goals-create_notifications'):
            return None

        # Make sure everything is ok before we run this.
        self.check()

        # Get the group of users for whom we're creating notifications
        users = self._get_users(options)

        # Schedules both dynamic notifications & non-dynamic ones.
        self.schedule_action_notifications(users)

        if waffle.switch_is_active('goals-customactions'):
            self.schedule_customaction_notifications()

        if waffle.switch_is_active('goals-morning-checkin'):
            self.schedule_morning_goal_notifications(users)
        if waffle.switch_is_active('goals-evening-checkin'):
            self.schedule_evening_goal_notifications(users)

        m = "Created {} notifications.".format(self._messages_created)
        self._log_messages.append((m, WARNING))
        self.write_log()
