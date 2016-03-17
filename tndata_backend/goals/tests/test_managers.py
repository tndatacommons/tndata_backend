from datetime import date, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

import pytz
from utils.user_utils import tzdt

from .. models import (
    Action,
    Behavior,
    Category,
    DailyProgress,
    Goal,
    Trigger,
    UserAction,
    UserBehavior
)
from .. settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_BEHAVIOR_TRIGGER_TIME,
    DEFAULT_BEHAVIOR_TRIGGER_RRULE,
    DEFAULT_MORNING_GOAL_TRIGGER_NAME,
    DEFAULT_MORNING_GOAL_TRIGGER_TIME,
    DEFAULT_MORNING_GOAL_TRIGGER_RRULE,
    DEFAULT_EVENING_GOAL_TRIGGER_NAME,
    DEFAULT_EVENING_GOAL_TRIGGER_TIME,
    DEFAULT_EVENING_GOAL_TRIGGER_RRULE,
)

User = get_user_model()


class TestUserActionManager(TestCase):

    def test_smoke(self):
        """A smoke test to ensure that chaining methods doesn't blow up."""
        self.assertEqual(list(UserAction.objects.published()), [])
        self.assertEqual(list(UserAction.objects.upcoming()), [])
        self.assertEqual(list(UserAction.objects.stale()), [])

        # And that chaining is possible
        qs = UserAction.objects.published().stale()
        self.assertEqual(list(qs), [])

        qs = UserAction.objects.published().upcoming()
        self.assertEqual(list(qs), [])


class TestCategoryManager(TestCase):
    """Tests for the `CategoryManager` manager."""

    @classmethod
    def setUpTestData(cls):
        cls.draft_category = Category.objects.create(
            order=1,
            title="Draft Category",
        )
        cls.published_category = Category.objects.create(
            order=2,
            title="Published Category",
            state="published"
        )
        cls.packaged_category = Category.objects.create(
            order=3,
            title="Packaged Category",
            state="published",
            packaged_content=True
        )

    def test_published(self):
        results = Category.objects.published()
        self.assertIn(self.published_category, results)
        self.assertNotIn(self.packaged_category, results)
        self.assertNotIn(self.draft_category, results)


class TestDailyProgressManager(TestCase):
    """Tests for the `DailyProgressManager` manager."""

    def test_exists_today(self):
        # When a user has no data
        u = User.objects.create_user('dp-exists', 'dp-exists@example.com', 'x')
        self.assertIsNone(DailyProgress.objects.exists_today(u))

        # When a user does have a DailyProgress instance
        dp = DailyProgress.objects.create(user=u)
        self.assertEqual(dp.id, DailyProgress.objects.exists_today(u))

        # clean up
        u.delete()
        dp.delete()

    def for_today(self):
        # When a user has no data
        u = User.objects.create_user('dp-exists', 'dp-exists@example.com', 'x')
        dp = DailyProgress.objects.for_today(u)
        self.assertEqual(dp.user, u)

        # When we fetch it again, it should return the same instance.
        other_dp = DailyProgress.objects.for_today(u)
        self.assertEqual(dp.id, other_dp.id)

        # clean up
        u.delete()
        dp.delete()


class TestGoalManager(TestCase):
    """Tests for the `GoalManager` manager."""

    @classmethod
    def setUpTestData(cls):
        cls.draft_category = Category.objects.create(
            order=1,
            title="Draft Category",
        )
        cls.published_category = Category.objects.create(
            order=2,
            title="Published Category",
            state="published"
        )
        cls.packaged_category = Category.objects.create(
            order=3,
            title="Packaged Category",
            state="published",
            packaged_content=True
        )

        cls.g1 = Goal.objects.create(title='One', state='published')
        cls.g1.categories.add(cls.draft_category)

        cls.g2 = Goal.objects.create(title='Two', state='published')
        cls.g2.categories.add(cls.published_category)

        cls.g3 = Goal.objects.create(title='Three', state='published')
        cls.g3.categories.add(cls.packaged_category)

    def test_published(self):
        """Published goals should exclude both unpublished categories and
        packaged content."""
        results = Goal.objects.published()
        self.assertEqual(list(results), [self.g2])

    def test_published_with_multiple_categories(self):
        """Test the case when a goal is part of a published Category AND
        is also in a published Package (Category). The .pubished() method should
        still return the goal.
        """
        # Create a goal that's in both a published package and category
        goal = Goal.objects.create(title='Dual Goal', state='published')
        goal.categories.add(self.published_category)
        goal.categories.add(self.packaged_category)

        # The goal should be in the set of published goals.
        self.assertIn(goal, Goal.objects.published())

    def test_packages(self):
        """The packages method should only return packaged content.
        It should also accept queryest parameters."""
        results = Goal.objects.packages()
        self.assertEqual(list(results), [self.g3])

        results = Goal.objects.packages(categories=self.packaged_category)
        self.assertEqual(list(results), [self.g3])

        results = Goal.objects.packages(categories=self.draft_category)
        self.assertEqual(list(results), [])


class TestTriggerManager(TestCase):
    """Tests for the `TriggerManager` manager."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("u", "u@a.com", "pass")

        cls.default_trigger = Trigger.objects.create(
            name="Default Trigger",
            time=time(12, 34),
            recurrences="RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        )

        cls.custom_trigger = Trigger.objects.create(
            user=cls.user,
            name="A Custom Trigger",
            trigger_date=date(2243, 7, 4),
            time=time(12, 34),
            recurrences="RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        )

    def test_get_default_behavior_trigger(self):
        # There is not default trigger at the moment, so calling this should
        # create one.
        t = Trigger.objects.get_default_behavior_trigger()
        self.assertEqual(t.name, DEFAULT_BEHAVIOR_TRIGGER_NAME)
        self.assertEqual(t.serialized_recurrences(), DEFAULT_BEHAVIOR_TRIGGER_RRULE)
        self.assertEqual(t.time.strftime("%H:%M"), DEFAULT_BEHAVIOR_TRIGGER_TIME)

        # Calling this again should return the original.
        obj = Trigger.objects.get_default_behavior_trigger()
        self.assertEqual(obj.id, t.id)

    def test_get_default_morning_goal_trigger(self):
        # There's no default trigger at the moment, so calling this creates one
        t = Trigger.objects.get_default_morning_goal_trigger()
        self.assertEqual(t.name, DEFAULT_MORNING_GOAL_TRIGGER_NAME)
        self.assertEqual(t.serialized_recurrences(), DEFAULT_MORNING_GOAL_TRIGGER_RRULE)
        self.assertEqual(t.time.strftime("%H:%M"), DEFAULT_MORNING_GOAL_TRIGGER_TIME)

        # Calling this again should return the original.
        obj = Trigger.objects.get_default_morning_goal_trigger()
        self.assertEqual(obj.id, t.id)

    def test_get_default_evening_goal_trigger(self):
        # There's no default trigger at the moment, so calling this creates one
        t = Trigger.objects.get_default_evening_goal_trigger()
        self.assertEqual(t.name, DEFAULT_EVENING_GOAL_TRIGGER_NAME)
        self.assertEqual(t.serialized_recurrences(), DEFAULT_EVENING_GOAL_TRIGGER_RRULE)
        self.assertEqual(t.time.strftime("%H:%M"), DEFAULT_EVENING_GOAL_TRIGGER_TIME)

        # Calling this again should return the original.
        obj = Trigger.objects.get_default_evening_goal_trigger()
        self.assertEqual(obj.id, t.id)

    def test_custom(self):
        """Ensure the custom method only returns custom triggers."""
        self.assertIn(self.custom_trigger, Trigger.objects.custom())
        self.assertNotIn(self.default_trigger, Trigger.objects.custom())

    def test_default(self):
        """Ensure the default method only returns default triggers."""
        self.assertIn(self.default_trigger, Trigger.objects.default())
        self.assertNotIn(self.custom_trigger, Trigger.objects.default())

    def test_for_user(self):
        """Ensure a user's triggers are returned."""
        self.assertIn(
            self.custom_trigger,
            Trigger.objects.for_user(self.user)
        )
        self.assertNotIn(
            self.default_trigger,
            Trigger.objects.for_user(self.user)
        )

    def test_create_for_user(self):
        with patch('goals.models.triggers.timezone') as mock_tz:
            mock_tz.is_naive = timezone.is_naive
            mock_tz.is_aware = timezone.is_aware
            mock_tz.make_aware = timezone.make_aware
            mock_tz.make_naive = timezone.make_naive
            mock_tz.utc = timezone.utc
            mock_tz.now.return_value = tzdt(2015, 3, 14, 8, 30)

            # When there's a time & recurrence
            trigger = Trigger.objects.create_for_user(
                self.user,
                "New Trigger",
                time(8, 30),
                None,
                "RRULE:FREQ=WEEKLY;BYDAY=MO",
            )
            self.assertEqual(
                trigger.recurrences_as_text(),
                "weekly, each Monday"
            )

            # when there's a time & a date
            trigger = Trigger.objects.create_for_user(
                self.user,
                "Other New Trigger",
                time(9, 30),
                date(2015, 3, 15),
                None
            )
            tz = pytz.timezone(self.user.userprofile.timezone)
            expected = tzdt(2015, 3, 15, 9, 30, tz=tz)
            self.assertEqual(
                trigger.next().strftime("%c %z"),
                expected.strftime("%c %z")
            )

    def test_create_for_userbehavior(self):
        b = Behavior.objects.create(title='Test Behavior')
        ub = UserBehavior.objects.create(user=self.user, behavior=b)

        trigger = Trigger.objects.create_for_user(
            self.user,
            ub.get_custom_trigger_name(),
            time(8, 30),
            None,
            "RRULE:FREQ=WEEKLY;BYDAY=MO",
            ub
        )

        ub = UserBehavior.objects.get(pk=ub.id)
        self.assertEqual(trigger.userbehavior_set.count(), 1)
        self.assertEqual(ub.custom_trigger, trigger)

        # Clean up
        ub.delete()
        b.delete()

    def test_create_for_useraction(self):
        b = Behavior.objects.create(title='Test Behavior')
        a = Action.objects.create(title='Test Action', behavior=b)
        ua = UserAction.objects.create(user=self.user, action=a)

        trigger = Trigger.objects.create_for_user(
            self.user,
            ua.get_custom_trigger_name(),
            time(8, 30),
            None,
            "RRULE:FREQ=WEEKLY;BYDAY=MO",
            ua
        )

        ua = UserAction.objects.get(pk=ua.id)
        self.assertEqual(trigger.useraction_set.count(), 1)
        self.assertEqual(ua.custom_trigger, trigger)

        # Clean up
        ua.delete()
        a.delete()
