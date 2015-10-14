from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from .. models import (
    Action,
    Behavior,
    Category,
    Goal,
    Trigger,
    UserAction,
    UserBehavior,
    UserCategory,
    UserCompletedAction,
    UserGoal,
)
from .. import user_feed


def tzdt(*args, **kwargs):
    """Return a timezone-aware datetime object."""
    tz = kwargs.pop("tz", timezone.utc)
    dt = datetime(*args)
    return timezone.make_aware(dt, timezone=tz)


class TestUserProgress(TestCase):
    """This test case sets up data for the user, and then proceeds to verify
    their progress info. It focuses on the following functions:

    * it runs the `aggregate_progress` management command
    * user_feed.action_feedback - Today's feedback data for an action.
    * user_feed.todays_actions_progress - The progress stats for today's
      scheduled actions.

    """

    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user('user', 'u@example.com', 'secret')

        # Create a Category/Goal/Behavior/Action(s) content
        cls.category = mommy.make(Category, title="CAT", state="published")
        cls.goal = mommy.make(Goal, title="GTITLE", state='published')
        cls.goal.categories.add(cls.category)
        cls.behavior = mommy.make(Behavior, title="BEH", state='published')
        cls.behavior.goals.add(cls.goal)
        cls.action1 = mommy.make(
            Action, title='A1', behavior=cls.behavior, state='published'
        )
        cls.action2 = mommy.make(
            Action, title='A2', behavior=cls.behavior, state='published'
        )
        cls.action3 = mommy.make(
            Action, title='A3', behavior=cls.behavior, state='published'
        )

        # Assign the user the above content
        cls.uc = mommy.make(UserCategory, user=cls.user, category=cls.category)
        cls.ug = mommy.make(UserGoal, user=cls.user, goal=cls.goal)
        cls.ub = mommy.make(UserBehavior, user=cls.user, behavior=cls.behavior)

        dt = timezone.now()
        cls.dt = tzdt(dt.year, dt.month, dt.day, 9, 0)  # Today, 9am
        with patch('goals.models.timezone.now') as mock_now:
            # Current time: 9am
            mock_now.return_value = cls.dt

            # Custom Triggers for each UserAction
            cls.t1 = Trigger.objects.create(
                user=cls.user,
                name="a1-trigger",
                trigger_type="time",
                time=time(22, 0),
                recurrences="RRULE:FREQ=DAILY"
            )
            cls.t2 = Trigger.objects.create(
                user=cls.user,
                name="a2-trigger",
                trigger_type="time",
                time=time(22, 30),
                recurrences="RRULE:FREQ=DAILY"
            )
            cls.t3 = Trigger.objects.create(
                user=cls.user,
                name="a3-trigger",
                trigger_type="time",
                time=time(23, 0),
                recurrences="RRULE:FREQ=DAILY"
            )

            # Create the UserActions
            cls.ua1 = UserAction.objects.create(
                user=cls.user,
                action=cls.action1,
                custom_trigger=cls.t1
            )
            cls.ua2 = UserAction.objects.create(
                user=cls.user,
                action=cls.action2,
                custom_trigger=cls.t2
            )
            cls.ua3 = UserAction.objects.create(
                user=cls.user,
                action=cls.action3,
                custom_trigger=cls.t3
            )

    @patch('sys.stderr')
    @patch('sys.stdout')
    def _run_refresh_useractions(self, mock_stderr, mock_stdout, dt=None):
        """Calls the `refresh_useractions` management command`."""
        timezone_path = 'goals.managers.timezone'
        log_path = "goals.management.commands.refresh_useractions.logger"
        with patch(log_path):
            with patch(timezone_path) as mock_timezone:
                if dt is None:
                    dt = self.dt  # today, 9am
                mock_timezone.now.return_value = dt
                call_command('refresh_useractions')

    @patch('sys.stderr')
    @patch('sys.stdout')
    def _run_aggregate_progress(self, mock_stderr, mock_stdout, dt=None):
        """Calls the `aggregate_progress` management command`."""
        timezone_path = 'goals.management.commands.aggregate_progress.timezone'
        log_path = "goals.management.commands.aggregate_progress.logger"
        with patch(log_path):
            with patch(timezone_path) as mock_timezone:
                if dt is None:
                    dt = self.dt  # today, 9am
                mock_timezone.now.return_value = dt
                call_command('aggregate_progress')

    def test_action_feedback_zero_percent(self):
        # Create some UserCompletedAction history for a single Action (10 days)
        with patch('goals.models.timezone.now') as mock_now:
            params = {
                'user': self.user,
                'useraction': self.ua1,
                'action': self.action1,
                'state': 'dismissed',
            }
            for d in range(1, 11):  # 10 days
                mock_now.reset_mock()
                mock_now.return_value = self.dt - timedelta(days=d)
                UserCompletedAction.objects.create(**params)

        self._run_aggregate_progress()
        results = user_feed.action_feedback(self.user, self.ua1)
        expected = {
            'title': "I've done some work to gtitle this month!",
            'subtitle': 'Even small steps can help me reach my goal',
            'total': 10,
            'completed': 0,
            'incomplete': 10,
            'percentage': 0,
        }
        self.assertEqual(results, expected)

    def test_action_feedback_half_completed(self):
        # Create some UserCompletedAction history for a single Action (10 days)
        with patch('goals.models.timezone.now') as mock_now:
            params = {
                'user': self.user,
                'useraction': self.ua1,
                'action': self.action1,
                'state': 'completed',
            }
            for d in range(1, 11):  # 10 days
                if d % 2 == 0:
                    params['state'] = 'dismissed'
                else:
                    params['state'] = 'completed'
                mock_now.reset_mock()
                mock_now.return_value = self.dt - timedelta(days=d)
                UserCompletedAction.objects.create(**params)

        self._run_aggregate_progress()
        results = user_feed.action_feedback(self.user, self.ua1)
        expected = {
            'title': "I've done 5 activities to gtitle this month!",
            'subtitle': 'I must really want this!',
            'total': 10,
            'completed': 5,
            'incomplete': 5,
            'percentage': 50,
        }
        self.assertEqual(results, expected)

    def test_action_feedback_sixty_percent(self):
        # Create some UserCompletedAction history for a single Action (10 days)
        with patch('goals.models.timezone.now') as mock_now:
            params = {
                'user': self.user,
                'useraction': self.ua1,
                'action': self.action1,
                'state': 'completed',
            }
            for d in range(1, 11):  # 10 days
                if d > 6:
                    params['state'] = 'dismissed'
                mock_now.reset_mock()
                mock_now.return_value = self.dt - timedelta(days=d)
                UserCompletedAction.objects.create(**params)

        self._run_aggregate_progress()
        results = user_feed.action_feedback(self.user, self.ua1)
        expected = {
            'title': "I've done 6 out of 10 activities to gtitle this month!",
            'subtitle': "I'm doing great! I'll schedule another activity!",
            'total': 10,
            'completed': 6,
            'incomplete': 4,
            'percentage': 60,
        }
        self.assertEqual(results, expected)

    def test_todays_actions_progress(self):
        with patch('goals.models.timezone.now') as mock_now:
            args = (self.dt.year, self.dt.month, self.dt.day, 9, 0)
            mock_now.return_value = tzdt(*args)
            params = {
                'user': self.user,
                'useraction': self.ua1,
                'action': self.action1,
                'state': 'completed',
            }
            # User has completed 2/3 of the actions.
            UserCompletedAction.objects.create(**params)
            params['useraction'] = self.ua2
            params['action'] = self.action2
            UserCompletedAction.objects.create(**params)
            params['useraction'] = self.ua3
            params['action'] = self.action3
            params['state'] = 'dismissed'
            UserCompletedAction.objects.create(**params)

        with patch('utils.user_utils.timezone') as mock_tz:
            # At 9am
            now = tzdt(self.dt.year, self.dt.month, self.dt.day, 9, 0)

            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            self._run_aggregate_progress(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # At 10pm
            mock_tz.reset_mock()
            now = tzdt(self.dt.year, self.dt.month, self.dt.day, 22, 0)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            self._run_aggregate_progress(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # At 11:45pm
            mock_tz.reset_mock()
            now = tzdt(self.dt.year, self.dt.month, self.dt.day, 23, 45)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            self._run_aggregate_progress(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # Next day at 12:02 am
            mock_tz.reset_mock()
            now = self.dt + timedelta(days=1)
            now = tzdt(now.year, now.month, now.day, 0, 2)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            self._run_aggregate_progress(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 0,
                'total': 0,
                'progress': 0,
            }
            self.assertEqual(progress, expected)


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
            fb['subtitle'], "Even small steps can help me reach my goal"
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
