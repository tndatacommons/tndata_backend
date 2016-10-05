from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from .. models import (
    Action,
    Category,
    CustomAction,
    CustomGoal,
    Goal,
    Trigger,
    UserAction,
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


class TestProgressStreaks(TestCase):

    def test__fil_streaks_with_exactly_seven(self):
        # Given exactly 7 values, we should get the same input as a result.
        data = [
            (date(2016, 8, 5), 4),
            (date(2016, 8, 6), 3),
            (date(2016, 8, 7), 4),
            (date(2016, 8, 8), 2),
            (date(2016, 8, 9), 6),
            (date(2016, 8, 10), 1),
            (date(2016, 8, 11), 7),
        ]
        with patch('utils.dateutils.timezone.now') as mock_now:
            mock_now.return_value = tzdt(2016, 8, 11, 9, 0)  # 9am
            self.assertEqual(list(user_feed._fill_streaks(data, days=7)), data)

    def test__fill_streaks_with_too_many(self):
        # Given 8 values, we want to keep 7. This should return the 7
        # most recent items in the list.
        data = [
            (date(2016, 8, 4), 21),
            (date(2016, 8, 5), 4),
            (date(2016, 8, 6), 3),
            (date(2016, 8, 7), 4),
            (date(2016, 8, 8), 2),
            (date(2016, 8, 9), 6),
            (date(2016, 8, 10), 1),
            (date(2016, 8, 11), 7),
        ]
        expected = [
            (date(2016, 8, 5), 4),
            (date(2016, 8, 6), 3),
            (date(2016, 8, 7), 4),
            (date(2016, 8, 8), 2),
            (date(2016, 8, 9), 6),
            (date(2016, 8, 10), 1),
            (date(2016, 8, 11), 7),
        ]
        with patch('utils.dateutils.timezone.now') as mock_now:
            mock_now.return_value = tzdt(2016, 8, 11, 9, 0)  # 9am
            self.assertEqual(list(user_feed._fill_streaks(data, days=7)), expected)

    def test__fill_streaks_with_too_few(self):
        # 4 values, we want 7
        data = [
            (date(2016, 8, 4), 21),
            (date(2016, 8, 7), 4),
            (date(2016, 8, 8), 2),
            (date(2016, 8, 11), 5),
        ]
        expected = [
            (date(2016, 8, 5), 0),
            (date(2016, 8, 6), 0),
            (date(2016, 8, 7), 4),
            (date(2016, 8, 8), 2),
            (date(2016, 8, 9), 0),
            (date(2016, 8, 10), 0),
            (date(2016, 8, 11), 5),
        ]
        with patch('utils.dateutils.timezone.now') as mock_now:
            mock_now.return_value = tzdt(2016, 8, 11, 9, 0)  # 9am
            self.assertEqual(list(user_feed._fill_streaks(data, days=7)), expected)


class TestUserProgress(TestCase):
    """This test case sets up data for the user, and then proceeds to verify
    their progress info. It focuses on the following functions:

    * user_feed.todays_actions_progress - The progress stats for today's
      scheduled actions.

    """

    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user('user', 'u@example.com', 'secret')
        # NOTE: User's default timezone is America/Chicago

        # Create a Category/Goal/Action(s) content
        cls.category = mommy.make(Category, title="CAT", state="published")
        cls.goal = mommy.make(Goal, title="GTITLE", state='published')
        cls.goal.categories.add(cls.category)
        cls.action1 = mommy.make(Action, title='A1', state='published')
        cls.action1.goals.add(cls.goal)
        cls.action2 = mommy.make(Action, title='A2', state='published')
        cls.action2.goals.add(cls.goal)
        cls.action3 = mommy.make(Action, title='A3', state='published')
        cls.action3.goals.add(cls.goal)

        # Assign the user the above content
        cls.uc = mommy.make(UserCategory, user=cls.user, category=cls.category)
        cls.ug = mommy.make(UserGoal, user=cls.user, goal=cls.goal)

        dt = timezone.now()
        cls.dt = tzdt(dt.year, dt.month, dt.day, 9, 0)  # Today, 9am
        with patch('goals.models.triggers.timezone.now') as mock_now:
            # Current time: 9am
            mock_now.return_value = cls.dt

            # Custom Triggers for each UserAction
            cls.t1 = Trigger.objects.create(
                user=cls.user,
                name="a1-trigger",
                time=time(22, 0),
                recurrences="RRULE:FREQ=DAILY"
            )
            cls.t2 = Trigger.objects.create(
                user=cls.user,
                name="a2-trigger",
                time=time(22, 30),
                recurrences="RRULE:FREQ=DAILY"
            )
            cls.t3 = Trigger.objects.create(
                user=cls.user,
                name="a3-trigger",
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

    def test_todays_actions_progress(self):
        with patch('django.utils.timezone.now') as mock_now:
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
            # At 9am UTC / 4am CDT / 3am CST
            now = tzdt(self.dt.year, self.dt.month, self.dt.day, 9, 0)

            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # At 10pm UTC / 5pm CDT / 4pm CST
            mock_tz.reset_mock()
            now = tzdt(self.dt.year, self.dt.month, self.dt.day, 22, 0)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # At 11:45pm UTC / 6:45 CDT / 5:45 CST
            mock_tz.reset_mock()
            now = tzdt(self.dt.year, self.dt.month, self.dt.day, 23, 45)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # Next day at 12am UTC / 7pm CDT / 6pm CST
            mock_tz.reset_mock()
            now = self.dt + timedelta(days=1)
            now = tzdt(now.year, now.month, now.day, 0, 0)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
            progress = user_feed.todays_actions_progress(self.user)
            expected = {
                'completed': 2,
                'total': 3,
                'progress': 66,
            }
            self.assertEqual(progress, expected)

            # Next day at 6:02am UTC / 1:02am CDT / 12:02am CST
            mock_tz.reset_mock()
            now = self.dt + timedelta(days=1)
            now = tzdt(now.year, now.month, now.day, 6, 2)
            mock_tz.now.return_value = now
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.is_naive = timezone.is_naive
            mock_tz.utc = timezone.utc

            self._run_refresh_useractions(dt=now)
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
        cls.goal.keywords = ['no_degree']  # will get matched; user has no info
        cls.goal.publish()
        cls.goal.save()

        # An Action
        cls.action = Action.objects.create(
            title="Test Action",
            sequence_order=1,
            goals=[cls.goal]
        )
        cls.action.publish()
        cls.action.save()

        # Give the user all the defined info.
        cls.uc = UserCategory.objects.create(user=cls.user, category=cls.category)
        cls.ug = UserGoal.objects.create(user=cls.user, goal=cls.goal)

        dt = timezone.now()
        with patch('goals.models.triggers.timezone.now') as mock_now:
            mock_now.return_value = tzdt(dt.year, dt.month, dt.day, 8, 0)
            # A Trigger for an action...
            cls.trigger = Trigger.objects.create(
                user=cls.user,
                name="test-trigger-for-action",
                time=time(22, 0),
                recurrences="RRULE:FREQ=DAILY"
            )
            cls.ua = UserAction.objects.create(
                user=cls.user,
                action=cls.action,
                custom_trigger=cls.trigger
            )

    def test_todays_actions_progress(self):
        resp = user_feed.todays_actions_progress(self.user)
        self.assertEqual(resp['completed'], 0)
        self.assertEqual(resp['total'], 1)
        self.assertEqual(resp['progress'], 0)

    def test_suggested_goals(self):
        # Create a new category
        cat = Category.objects.create(order=2, title="Other")
        cat.publish()
        cat.save()

        # Ensure it's selected by the user
        UserCategory.objects.create(user=self.user, category=cat)

        # Create a Goal in that category (with appropriate keywords)
        goal = Goal.objects.create(
            title='Other Goal',
            state='published',
            keywords=['no_job', 'no_child']
        )
        goal.categories.add(cat)

        # User should receive it as a suggestion
        suggestions = user_feed.suggested_goals(self.user)
        self.assertEqual(list(suggestions), [])  # XXX: because these are disabled

    def test_selected_goals(self):
        self.assertEqual(
            user_feed.selected_goals(self.user),
            [(0, self.ug)]
        )

    def test_feed_data_with_custom_actions(self):
        """Ensure that feed_data works when a user has a CustomAction with
        a corresponding CustomGoal, as well as a CustomAction tied to an
        existnig Goal."""
        ca_with_goal = CustomAction.objects.create(
            user=self.user,
            goal=self.goal,
            title="Custom Action with Goal",
            next_trigger_date=timezone.now() + timedelta(minutes=5)
        )

        custom_goal = CustomGoal.objects.create(user=self.user, title="Custom Goal")
        ca_with_custom_goal = CustomAction.objects.create(
            user=self.user,
            customgoal=custom_goal,
            title="Custom Action with Custom Goal",
            next_trigger_date=timezone.now() + timedelta(minutes=5)
        )
        data = user_feed.feed_data(self.user)

        # Pull all the titles from the upcoming actions
        upcoming = [a['action'] for a in data['upcoming']]
        self.assertIn(ca_with_goal.title, upcoming)
        self.assertIn(ca_with_custom_goal.title, upcoming)
