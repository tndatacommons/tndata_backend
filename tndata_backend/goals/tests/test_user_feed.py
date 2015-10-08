from datetime import datetime, time
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from .. models import (
    Action,
    Behavior,
    Category,
    Goal,
    Trigger,
    UserAction,
    UserBehavior,
    UserCategory,
    UserGoal,
)
from .. import user_feed


def tzdt(*args, **kwargs):
    """Return a timezone-aware datetime object."""
    tz = kwargs.pop("tz", timezone.utc)
    dt = datetime(*args)
    return timezone.make_aware(dt, timezone=tz)


class TestUserFeed(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user('user', 'u@example.com', 'secret')

        # Create a Category
        cls.category = Category.objects.create(order=1, title='Test Category')
        cls.category.publish()
        cls.category.save()

        # A Goal
        cls.goal = Goal.objects.create(title="Test Goal")
        cls.goal.categories.add(cls.category)
        cls.goal.publish()
        cls.goal.save()

        # A Behavior
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.behavior.goals.add(cls.goal)
        cls.behavior.publish()
        cls.behavior.save()

        # An Action
        cls.action = Action.objects.create(
            title="Test Action",
            sequence_order=1,
            behavior=cls.behavior
        )
        cls.action.publish()
        cls.action.save()

        # Give the user all the defined info.
        cls.uc = UserCategory.objects.create(user=cls.user, category=cls.category)
        cls.ug = UserGoal.objects.create(user=cls.user, goal=cls.goal)
        cls.ub = UserBehavior.objects.create(user=cls.user, behavior=cls.behavior)

        dt = timezone.now()
        with patch('goals.models.timezone.now') as mock_now:
            mock_now.return_value = tzdt(dt.year, dt.month, dt.day, 0, 5)
            # A Trigger for an action...
            cls.trigger = Trigger.objects.create(
                user=cls.user,
                name="test-trigger-for-action",
                trigger_type="time",
                time=time(22, 0),
                recurrences="RRULE:FREQ=DAILY"
            )
            cls.ua = UserAction.objects.create(
                user=cls.user,
                action=cls.action,
                custom_trigger=cls.trigger
            )

    def test_action_feedback(self):
        # We have no UserCompletedAction objects, so this should be < 20%
        fb = user_feed.action_feedback(self.user, self.ua)
        self.assertEqual(fb['completed'], 0)
        self.assertEqual(fb['incomplete'], 0)
        self.assertEqual(fb['percentage'], 0)
        self.assertEqual(
            fb['title'], "I've done some work to test goal this month!"
        )
        self.assertEqual(
            fb['subtitle'], "Every action taken brings me closer"
        )

    def test_todays_actions(self):
        dt = timezone.now()
        with patch('goals.user_feed.timezone.now') as mock_now:
            mock_now.return_value = tzdt(dt.year, dt.month, dt.day, 11, 0)
            result = user_feed.todays_actions(self.user)
            self.assertEqual(list(result), [self.ua])

    def test_todays_actions_progress(self):
        resp = user_feed.todays_actions_progress(self.user)
        self.assertEqual(resp['completed'], 0)
        self.assertEqual(resp['total'], 1)
        self.assertEqual(resp['progress'], 0)

    def test_next_user_action(self):
        dt = timezone.now()
        with patch('goals.user_feed.timezone.now') as mock_now:
            mock_now.return_value = tzdt(dt.year, dt.month, dt.day, 11, 10)
            ua = user_feed.next_user_action(self.user)
            self.assertEqual(ua, self.ua)

    def test_suggested_goals(self):
        suggestions = user_feed.suggested_goals(self.user)
        self.assertEqual(list(suggestions), [self.goal])

    def test_selected_goals(self):
        self.assertEqual(
            user_feed.selected_goals(self.user),
            [(0, self.ug)]
        )
