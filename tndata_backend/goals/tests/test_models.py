import pytz
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.db.models import QuerySet
from django.utils import timezone

from model_mommy import mommy
from utils.user_utils import tzdt

from .. models import (
    Action,
    Behavior,
    Category,
    CustomAction,
    CustomActionFeedback,
    CustomGoal,
    DailyProgress,
    Goal,
    PackageEnrollment,
    Trigger,
    UserAction,
    UserBehavior,
    UserCategory,
    UserCompletedAction,
    UserCompletedCustomAction,
    UserGoal,
)

User = get_user_model()


class TestCaseDates(TestCase):
    """A test case with additional methods for testing dates and datetimes"""

    def assertDatesEqual(self, dt1, dt2):
        self.assertEqual(
            dt1.strftime("%Y-%m-%d %z %Z"),
            dt2.strftime("%Y-%m-%d %z %Z")
        )

    def assertDatetimesEqual(self, dt1, dt2):
        self.assertEqual(
            dt1.strftime("%Y-%m-%d %H:%M:%S %z %Z"),
            dt2.strftime("%Y-%m-%d %H:%M:%S %z %Z")
        )


class TestCategory(TestCase):
    """Tests for the `Category` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()

    def test__str__(self):
        expected = "Test Category"
        actual = "{}".format(self.category)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        category = Category.objects.create(order=2, title="New Name")
        category.save()
        self.assertEqual(category.title_slug, "new-name")
        category.delete()  # Clean up.

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        c = Category(order=3, title="New")
        c.save(created_by=u)
        self.assertEqual(c.created_by, u)
        u.delete()  # Clean up
        c.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.category.save(updated_by=u)
        self.assertEqual(self.category.updated_by, u)
        u.delete()  # Clean up

    def test_goals(self):
        self.assertIsInstance(self.category.goals, QuerySet)

    def test_behaviors(self):
        self.assertIsInstance(self.category.behaviors, QuerySet)

    def test__format_color(self):
        self.assertEqual(self.category._format_color("ffaabb"), "#ffaabb")
        self.assertEqual(self.category._format_color("#ffaabb"), "#ffaabb")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.category.get_absolute_url(),
            "/goals/categories/{0}-test-category/".format(self.category.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.category.get_update_url(),
            "/goals/categories/{0}-test-category/update/".format(self.category.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.category.get_delete_url(),
            "/goals/categories/{0}-test-category/delete/".format(self.category.id)
        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.category.state, "draft")

    def test_review(self):
        self.category.review()  # Switch to pending-review
        self.assertEqual(self.category.state, "pending-review")

    def test_decline(self):
        self.category.review()  # Switch to pending-review
        self.category.decline()  # then decline
        self.assertEqual(self.category.state, "declined")

    def test_publish(self):
        self.category.review()  # Switch to pending-review
        self.category.publish()  # then publish
        self.assertEqual(self.category.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.category.state, "draft")
        self.category.publish()  # then publish
        self.assertEqual(self.category.state, "published")

    def test_is_packaged(self):
        # Our default category
        self.assertFalse(self.category.is_packaged)

        # An actual package
        c = Category.objects.create(
            order=3,
            title="Some Package",
            packaged_content=True
        )
        self.assertTrue(c.is_packaged)
        c.delete()

    def test_clean_title_on_save(self):
        self.category.title = "    A NEW title."
        self.category.save()
        self.assertEqual(self.category.title, "A NEW title")

    def test_clean_description_on_save(self):
        self.category.description = "  more descriptions.   "
        self.category.save()
        self.assertEqual(self.category.description, "more descriptions.")


class TestGoal(TestCase):
    """Tests for the `Goal` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        self.goal.categories.add(self.category)

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Category.objects.filter(id=self.category.id).delete()

    def test__str__(self):
        expected = "Title for Test Goal"
        actual = "{}".format(self.goal)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        goal = Goal.objects.create(title="New Name")
        goal.save()
        self.assertEqual(goal.title_slug, "new-name")

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        g = Goal(title="New")
        g.save(created_by=u)
        self.assertEqual(g.created_by, u)
        u.delete()  # Clean up
        g.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.goal.save(updated_by=u)
        self.assertEqual(self.goal.updated_by, u)
        u.delete()  # Clean up

    def test_get_absolute_url(self):
        self.assertEqual(
            self.goal.get_absolute_url(),
            "/goals/goals/{0}-title-for-test-goal/".format(self.goal.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.goal.get_update_url(),
            "/goals/goals/{0}-title-for-test-goal/update/".format(self.goal.id)

        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.goal.get_delete_url(),
            "/goals/goals/{0}-title-for-test-goal/delete/".format(self.goal.id)

        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.goal.state, "draft")

    def test_review(self):
        self.goal.review()  # Switch to pending-review
        self.assertEqual(self.goal.state, "pending-review")

    def test_decline(self):
        self.goal.review()  # Switch to pending-review
        self.goal.decline()  # then decline
        self.assertEqual(self.goal.state, "declined")

    def test_publish(self):
        self.goal.review()  # Switch to pending-review
        self.goal.publish()  # then publish
        self.assertEqual(self.goal.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.goal.state, "draft")
        self.goal.publish()  # then publish
        self.assertEqual(self.goal.state, "published")

    def test_clean_title_on_save(self):
        self.goal.title = "    A NEW title."
        self.goal.save()
        self.assertEqual(self.goal.title, "A NEW title")

    def test_clean_description_on_save(self):
        self.goal.description = "  more descriptions.   "
        self.goal.save()
        self.assertEqual(self.goal.description, "more descriptions.")


class TestGoalEnrollment(TestCase):
    """This is a set of integration tests for Goal.enroll -- i.e. goal
    enrollment."""

    @classmethod
    def setUpTestData(cls):
        # Create a user.
        User = get_user_model()
        cls.user = User.objects.create_user("u", "u@example.com", "lsdjf")

        def _t():
            # Function to generate a trigger
            return mommy.make(Trigger, time_of_day='morning', frequency='daily')

        def _goal(title, category, seq):  # creates a published Goal
            return mommy.make(
                Goal,
                title=title,
                sequence_order=seq,
                state='published',
                categories=[category]
            )

        def _behavior(title, goal, seq):  # creates a published Behavior
            return mommy.make(
                Behavior,
                title=title,
                sequence_order=seq,
                state='published',
                goals=[goal]
            )

        def _action(title, behavior, seq):  # creates a published Action
            return mommy.make(
                Action,
                title=title,
                sequence_order=seq,
                behavior=behavior,
                default_trigger=_t(),
                state='published'
            )

        # Create the content of library for the user.
        cls.cat = mommy.make(
            Category, title="C", featured=True,
            order=0, state='published'
        )

        # Create Goals
        cls.goal1 = _goal('G1', cls.cat, 0)
        cls.goal2 = _goal('G2', cls.cat, 0)

        # and behaviors

        b1 = _behavior("B1", cls.goal1, 0)
        b2 = _behavior("B2", cls.goal2, 0)

        # and actions
        _action("A10", b1, 0)
        _action("A11", b1, 1)
        _action("A20", b2, 0)
        _action("A21", b2, 1)

    def tearDown(self):
        # Rest user-selected content
        UserAction.objects.all().delete()
        UserBehavior.objects.all().delete()
        UserGoal.objects.all().delete()
        UserCategory.objects.all().delete()

    def test_enroll_with_primary_category(self):
        # Enroll the user in the first goal, specify the category
        self.goal1.enroll(self.user, primary_category=self.cat)

        # ensure the content got added.
        categories = self.user.usercategory_set.values_list(
            'category__title', flat=True)
        goals = self.user.usergoal_set.values_list('goal__title', flat=True)
        behaviors = self.user.userbehavior_set.values_list(
            'behavior__title', flat=True)
        actions = self.user.useraction_set.values_list(
            'action__title', flat=True)

        self.assertEqual(sorted(list(categories)), ['C'])
        self.assertEqual(sorted(list(goals)), ['G1'])
        self.assertEqual(sorted(list(behaviors)), ['B1'])
        self.assertEqual(sorted(list(actions)), ['A10', 'A11'])

    def test_enroll_without_primary_category(self):
        # Enroll the user in the second goal, but don't specify the category
        self.goal2.enroll(self.user)

        # ensure the content got added.
        categories = self.user.usercategory_set.values_list(
            'category__title', flat=True)
        goals = self.user.usergoal_set.values_list('goal__title', flat=True)
        behaviors = self.user.userbehavior_set.values_list(
            'behavior__title', flat=True)
        actions = self.user.useraction_set.values_list(
            'action__title', flat=True)

        self.assertEqual(sorted(list(categories)), ['C'])
        self.assertEqual(sorted(list(goals)), ['G2'])
        self.assertEqual(sorted(list(behaviors)), ['B2'])
        self.assertEqual(sorted(list(actions)), ['A20', 'A21'])


class TestTrigger(TestCase):
    """Tests for the `Trigger` model."""

    @classmethod
    def setUpTestData(cls):
        cls.trigger = Trigger.objects.create(
            name="Test Trigger",
            time=time(12, 34),
            recurrences="RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        )

    def test_recurrences_formats(self):
        """Test various recurrences formats"""
        payload = {
            "name": "A",
            "time": time(12, 34),
            "recurrences": "RRULE:FREQ=DAILY"
        }
        t = Trigger.objects.create(**payload)
        self.assertEqual(t.serialized_recurrences(), "RRULE:FREQ=DAILY")

        payload["name"] = "B"
        payload["recurrences"] = "RRULE:FREQ=WEEKLY;WKST=SU;BYDAY=MO,TU,WE,TH,FR"
        t = Trigger.objects.create(**payload)
        self.assertEqual(
            t.serialized_recurrences(),
            "RRULE:FREQ=WEEKLY;WKST=SU;BYDAY=MO,TU,WE,TH,FR"
        )

    def test__str__(self):
        expected = (
            "Test Trigger\n"
            "12:34:00+00:00\n"
            "weekly, each Monday, Tuesday, Wednesday, Thursday, Friday\n"
        )
        self.assertEqual("{}".format(self.trigger), expected)

    def test_time_details(self):
        trigger = Trigger.objects.create(
            name="TESTing trigger time details",
            time=time(12, 34),
            recurrences="RRULE:FREQ=WEEKLY;WKST=SU;BYDAY=MO"
        )
        expected = "12:34:00+00:00\nweekly, each Monday\n"
        self.assertEqual(trigger.time_details, expected)
        Trigger.objects.filter(id=trigger.id).delete()

    def test__localize_time(self):
        t = Trigger(name="X", time=time(12, 34))
        self.assertEqual(t.time, time(12, 34))
        t._localize_time()
        self.assertEqual(t.time, time(12, 34, tzinfo=timezone.utc))

    def test_save(self):
        """Verify that saving generates a name_slug"""
        trigger = Trigger.objects.create(name="New Name")
        trigger.save()
        self.assertEqual(trigger.name_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.trigger.get_absolute_url(),
            "/goals/triggers/{0}/".format(self.trigger.id)

        )

    def test_recurrences_as_text(self):
        expected = "weekly, each Monday, Tuesday, Wednesday, Thursday, Friday"
        self.assertEqual(self.trigger.recurrences_as_text(), expected)

    def test__combine(self):
        """Ensure the Trigger.__combine wrapper works as expected."""

        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 2)
            t = self.trigger._combine(time(13, 30))
            self.assertEqual(t, tzdt(2015, 1, 2, 13, 30))

            t = self.trigger._combine(time(13, 30), date(2015, 2, 3))
            self.assertEqual(t, tzdt(2015, 2, 3, 13, 30))

            tz = pytz.timezone("America/Chicago")
            t = self.trigger._combine(time(13, 30), date(2010, 12, 30), tz)
            self.assertEqual(t, tzdt(2010, 12, 30, 13, 30, tz=tz))

    def test_get_tz_without_user(self):
        """Ensure this returns the appropriate timezone."""
        self.assertIsNone(self.trigger.user)
        self.assertEqual(self.trigger.get_tz(), timezone.utc)

    def test_get_tz_with_user(self):
        """Ensure this returns the user's selected timezone."""
        u = User.objects.create_user("get_tz_uer", "get_tz_user@example.com", "s")
        u.userprofile.timezone = "America/Chicago"
        t = Trigger.objects.create(
            user=u,
            name="User's test Trigger",
            time=time(12, 34),
        )

        self.assertEqual(t.get_tz(), pytz.timezone("America/Chicago"))

        # clean up
        u.delete()
        t.delete()

    def test_get_alert_time(self):
        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 2)

            # No date, should combine "now" + time
            self.assertEqual(
                self.trigger.get_alert_time(),
                tzdt(2015, 1, 2, 12, 34)
            )

            # Date + time should get combined.
            self.trigger.trigger_date = date(2015, 3, 15)
            self.trigger.save()
            self.assertEqual(
                self.trigger.get_alert_time(),
                tzdt(2015, 3, 15, 12, 34)
            )

            # No date or time should return None
            self.assertIsNone(Trigger().get_alert_time())

    def test_get_occurences_when_disabled(self):
        trigger = mommy.make(Trigger, disabled=True)
        self.assertEqual(trigger.get_occurences(), [])
        trigger.delete()

    def test__stopped_by_completion__default_trigger(self):
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)
        beh = mommy.make(Behavior, title="Beh", state="published")
        beh.goals.add(goal)

        trigger = mommy.make(
            Trigger,
            name="StopTrigger",
            time=time(17, 0),
            recurrences="RRULE:FREQ=DAILY",
            stop_on_complete=True,
        )
        act = mommy.make(
            Action,
            behavior=beh,
            title='Act',
            state='published',
            default_trigger=trigger
        )

        user = mommy.make(User)
        ua = mommy.make(UserAction, action=act, user=user)
        self.assertFalse(trigger._stopped_by_completion(user))

        # now the user has completed the action
        mommy.make(
            UserCompletedAction,
            user=user,
            useraction=ua,
            action=act,
            state='completed'
        )
        self.assertTrue(trigger._stopped_by_completion(user))

    def test__stopped_by_completion__custom_trigger(self):
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)
        beh = mommy.make(Behavior, title="Beh", state="published")
        beh.goals.add(goal)
        act = mommy.make(Action, behavior=beh, title='Act', state='published')

        user = mommy.make(User)
        trigger = mommy.make(
            Trigger,
            name="StopTrigger",
            time=time(17, 0),
            recurrences="RRULE:FREQ=DAILY",
            stop_on_complete=True,
            user=user
        )
        ua = mommy.make(UserAction, user=user, action=act, custom_trigger=trigger)
        self.assertFalse(trigger._stopped_by_completion(user))

        # now the user has completed the action
        mommy.make(
            UserCompletedAction,
            user=user,
            useraction=ua,
            action=ua.action,
            state='completed'
        )
        self.assertTrue(trigger._stopped_by_completion(user))

    def test_is_dynamic(self):
        # False when there's no frequency or time_of_day
        self.assertFalse(self.trigger.is_dynamic)

        # True when there is both frequency or time_of_day
        trigger = mommy.make(Trigger, frequency='daily', time_of_day='early')
        self.assertTrue(trigger.is_dynamic)

    def test_dynamic_range(self):
        """Ensure we get the correct range of valid dates for dynamic triggers"""

        # None when not dynamic
        self.assertIsNone(self.trigger.dynamic_range())

        # None when no user
        trigger = mommy.make(Trigger, frequency='daily', time_of_day='early')
        self.assertIsNone(trigger.dynamic_range())

        # When we have a user...
        trigger.user = mommy.make(User)
        trigger.save()

        with patch("goals.models.triggers.local_now") as mock_now:
            mock_now.return_value = tzdt(2016, 4, 1, 12, 34, 56)

            # Daily - 1 day
            expected = (tzdt(2016, 4, 1, 5, 0), tzdt(2016, 4, 3, 4, 59, 59, 999999))
            self.assertEqual(trigger.dynamic_range(), expected)

            # Weekly - 7 days
            trigger.frequency = 'weekly'
            trigger.save()
            expected = (tzdt(2016, 4, 1, 5, 0), tzdt(2016, 4, 9, 4, 59, 59, 999999))
            self.assertEqual(trigger.dynamic_range(), expected)

            # Biweekly - 5 days
            trigger.frequency = 'biweekly'
            trigger.save()
            expected = (tzdt(2016, 4, 1, 5, 0), tzdt(2016, 4, 7, 4, 59, 59, 999999))
            self.assertEqual(trigger.dynamic_range(), expected)

            # Multiweekly - 5 days
            trigger.frequency = 'multiweekly'
            trigger.save()
            expected = (tzdt(2016, 4, 1, 5, 0), tzdt(2016, 4, 7, 4, 59, 59, 999999))
            self.assertEqual(trigger.dynamic_range(), expected)

            # Weekends - Depends on the day, but encompases the updcoming weekend.
            # April, 2016, 1st = Friday, Sunday = 3rd
            trigger.frequency = 'weekends'
            trigger.save()
            expected = (tzdt(2016, 4, 1, 5, 0), tzdt(2016, 4, 4, 4, 59, 59, 999999))
            self.assertEqual(trigger.dynamic_range(), expected)

    def test_dynamic_trigger_date(self):
        # is None when not dynamic
        self.assertIsNone(self.trigger.dynamic_trigger_date())

        # returns None there's no user
        trigger = mommy.make(Trigger, frequency="daily", time_of_day='early')
        self.assertIsNone(trigger.dynamic_trigger_date())

        # Returns a datetime object when there is a user.
        trigger.user = mommy.make(User)
        trigger.save()
        self.assertIsNotNone(trigger.dynamic_trigger_date())
        trigger.delete()

    def test_dynamic_trigger_date_hours(self):
        """Ensure that this method returns the correct values for different
        time_of_day values based on the user's selected timezone."""

        user = mommy.make(User)
        user.userprofile.timezone = "America/Chicago"
        user.userprofile.save()

        kwargs = {'frequency': 'daily', 'time_of_day': 'early', 'user': user}
        trigger = mommy.make(Trigger, **kwargs)

        # Ensure the result is in the user's local timezone.
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        timezones = set([t.tzname() for t in times])
        self.assertTrue(timezones.issubset({'CDT', 'CST'}))

        # Ensure early times are in [6, 7, 8]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {6, 7, 8})

        # Ensure morning times are in [9, 10, 11]
        kwargs['time_of_day'] = 'morning'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {9, 10, 11})

        # Ensure noonish times are in [11, 12, 13]
        kwargs['time_of_day'] = 'noonish'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {11, 12, 13})

        # Ensure afternoon times are in [13, 14, 15, 16, 17]
        kwargs['time_of_day'] = 'afternoon'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {13, 14, 15, 16, 17})

        # Ensure evening times are in [17, 18, 19, 20, 21]
        kwargs['time_of_day'] = 'evening'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {17, 18, 19, 20, 21})

        # Ensure late times are in [22, 23, 0, 1, 2]
        kwargs['time_of_day'] = 'late'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {22, 23, 0, 1, 2})

        # clean up
        trigger.delete()
        user.delete()

    def test_next_when_disabled(self):
        trigger = mommy.make(
            Trigger,
            name="A disabled Trigger",
            time=time(12, 34),
            recurrences="RRULE:FREQ=DAILY",
            disabled=True
        )
        self.assertIsNone(trigger.next())

    def test_next_when_no_time_or_date(self):
        """Ensure that next none when there's no time, recurrence, or date"""
        self.assertIsNone(Trigger().next())

    def test_next(self):
        trigger = Trigger.objects.create(
            name="Daily Test Trigger",
            time=time(12, 34),
            recurrences="RRULE:FREQ=DAILY",
        )
        with patch("goals.models.triggers.timezone.now") as mock_now:
            # Ensure we get the *today* if it's scheduled later in the day
            # now is 9:30 am, trigger is for 12:34pm
            mock_now.return_value = tzdt(1000, 10, 20, 9, 30)
            expected = tzdt(1000, 10, 20, 12, 34)
            self.assertEqual(trigger.next(), expected)

            # Ensure we get the next day's trigger if later than *now*
            # now is 1:30pm, trigger is for 12:34pm
            mock_now.return_value = tzdt(1000, 10, 20, 13, 30)
            expected = tzdt(1000, 10, 21, 12, 34)
            self.assertEqual(trigger.next(), expected)

            # Ensure we get the same day's trigger if the times matche
            # now is 12:34pm, trigger is for 12:34pm
            mock_now.return_value = tzdt(1000, 10, 20, 12, 34)
            expected = tzdt(1000, 10, 20, 12, 34)
            self.assertEqual(trigger.next(), expected)

        # Clean up
        trigger.delete()

    def test_next_with_stop_on_complete(self):
        """Ensure that a trigger a stop_on_complete set will no longer return
        dates after it has "stopped"."""
        trigger = Trigger.objects.create(
            name="Stop-Trigger",
            time=time(12, 34),
            trigger_date=date(2015, 1, 1),
            stop_on_complete=True
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 1, 9, 0)

            # First, when the trigger hasn't been stopped.
            trigger._stopped_by_completion = Mock(return_value=False)
            expected = tzdt(2015, 1, 1, 12, 34)
            expected = expected.strftime("%c %z")
            actual = trigger.next().strftime("%c %z")
            self.assertEqual(actual, expected)

            # Now once the trigger has been completed
            trigger._stopped_by_completion = Mock(return_value=True)
            self.assertIsNone(trigger.next())

    def test_next_when_no_recurrence(self):
        """Ensure that a trigger without a recurrence, but with a time & date
        yields the correct value via it's `next` method."""
        trigger = Trigger.objects.create(
            name="Date-Trigger",
            time=time(12, 34),
            trigger_date=date(2222, 3, 15),
        )

        # When the date is far in the future, we should get that future date.
        expected = datetime.combine(date(2222, 3, 15), time(12, 34))
        expected = timezone.make_aware(expected, timezone=timezone.utc)
        self.assertEqual(trigger.next(), expected)

        # When the set date is in the past, we should not get a value.
        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = datetime(
                2222, 3, 16, 6, 0, tzinfo=timezone.utc
            )
            self.assertIsNone(trigger.next())

    def test_next_with_until_date(self):
        """Test the value of `next`, when the recurrence has a stop date."""
        # daily, until 2015-08-31 at 12:30pm
        rrule = 'RRULE:FREQ=DAILY;UNTIL=20150831T050000Z'
        t = Trigger.objects.create(
            name="x",
            time=time(12, 30),
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 2015-08-15 at 11:00am
            # expected: same day, at appointed time
            mock_now.return_value = datetime(
                2015, 8, 15, 11, 0, tzinfo=timezone.utc
            )
            expected = datetime(2015, 8, 15, 12, 30, tzinfo=timezone.utc)
            self.assertEqual(t.next(), expected)

            # now: 2015-08-15 at 2:00pm
            # expected: next day, at appointed time
            mock_now.return_value = datetime(
                2015, 8, 15, 14, 0, tzinfo=timezone.utc
            )
            expected = datetime(2015, 8, 16, 12, 30, tzinfo=timezone.utc)
            self.assertEqual(t.next(), expected)

            # now: 2015-09-01 at 11:00am
            # expected: None because we're past the "until date"
            mock_now.return_value = datetime(
                2015, 9, 1, 11, 0, tzinfo=timezone.utc
            )
            self.assertIsNone(t.next())

        # Clean up
        t.delete()

    def test_next_with_a_count(self):
        """Test the value of `next`, when the recurrence is set to occure a
        set number of times (with COUNT in the RRULE)."""
        # daily, occuring once
        rrule = 'RRULE:FREQ=DAILY;COUNT=1'
        t = Trigger.objects.create(
            name="x",
            time=time(12, 30),
            trigger_date=date(2015, 8, 2),
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 2015-08-01 at 11:00am
            # expected: 2015-08-02, at 12:30pm
            mock_now.return_value = tzdt(2015, 8, 1, 11, 0)
            expected = tzdt(2015, 8, 2, 12, 30)
            self.assertEqual(t.next(), expected)

            # now: 2015-08-02 at 9:00am
            # expected: 2015-08-02 at 12:30pm
            mock_now.return_value = tzdt(2015, 8, 2, 9, 0)
            expected = tzdt(2015, 8, 2, 12, 30)
            self.assertEqual(t.next(), expected)

            # now: 2015-08-02 at 12:30pm
            # expected: 2015-08-02 at 12:30pm
            mock_now.return_value = tzdt(2015, 8, 2, 12, 30)
            expected = tzdt(2015, 8, 2, 12, 30)
            self.assertEqual(t.next(), expected)

            # now: 2015-08-03 at 9:00am  (the day after)
            # expected: None because it's already fired once.
            mock_now.return_value = tzdt(2015, 8, 3, 9, 0)
            self.assertIsNone(t.next())

        # Clean up
        t.delete()

    def test_next_with_daily_interval(self):
        """Test the value of `next`, when the recurrence is for every other day."""
        # every other day
        rrule = 'RRULE:FREQ=DAILY;INTERVAL=2'
        t = Trigger.objects.create(
            name="x",
            time=time(12, 30),
            trigger_date=date(2015, 8, 1),
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 2015-08-01 at 11:00am
            # expected: same day, at 12:30pm
            mock_now.return_value = datetime(
                2015, 8, 1, 11, 0, tzinfo=timezone.utc
            )
            expected = datetime(2015, 8, 1, 12, 30, tzinfo=timezone.utc)
            self.assertEqual(t.next(), expected)

            # now: 2015-08-02 at 11:00am
            # expected: Tomorrow (8/3) at 12:30
            mock_now.return_value = datetime(
                2015, 8, 2, 11, 0, tzinfo=timezone.utc
            )
            expected = datetime(2015, 8, 3, 12, 30, tzinfo=timezone.utc)
            self.assertEqual(t.next(), expected)

            # the next day: 2015-08-03 at 5:00pm
            # expected: the next day (8/5) at 12:30 (becase it's past today's)
            mock_now.return_value = datetime(
                2015, 8, 3, 17, 0, tzinfo=timezone.utc
            )
            expected = datetime(2015, 8, 5, 12, 30, tzinfo=timezone.utc)
            self.assertEqual(t.next(), expected)

        # Clean up
        t.delete()

    def test_next_with_future_date(self):
        """Test the value of `next`, when the recurrence has a trigger_date,
        that's set in the future."""

        # Repeat daily at 9:00am, starting Oct 1, 2015
        rrule = 'RRULE:FREQ=DAILY'
        t = Trigger.objects.create(
            name="x",
            time=time(9, 0),
            trigger_date=date(2015, 10, 1),
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 2015-08-15 at 11:00am, expected: next is 10/1
            mock_now.return_value = tzdt(2015, 8, 15, 11, 0)
            expected = tzdt(2015, 10, 1, 9, 0)
            self.assertEqual(t.next(), expected)

            # Should work as normal after the start date.
            # now: 2015-10-2 at 11:00am, expected next is 10/3 9am
            mock_now.return_value = tzdt(2015, 10, 2, 11, 0)
            expected = tzdt(2015, 10, 3, 9, 0)
            self.assertEqual(t.next(), expected)

        # Clean up
        t.delete()

    def test_next_for_three_days(self):
        """Test the value of `next` for recurrences that specify a distinct
        set of days."""

        # 7pm on M, W, Th on Aug 17, 19, 20  (repeat until 8/21/2015)
        rrule = 'RRULE:FREQ=WEEKLY;UNTIL=20150821T050000Z;BYDAY=MO,WE,TH'
        t = Trigger.objects.create(
            name="x",
            time=time(19, 0),
            trigger_date=date(2015, 8, 17),
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 08/15 at 11:00am, expected: next is Mon 8/17
            mock_now.return_value = tzdt(2015, 8, 15, 11, 0)
            expected = tzdt(2015, 8, 17, 19, 0)
            self.assertEqual(t.next(), expected)

            # now: 8/17 at 11:00pm, expected next is 8/19 at 7pm
            mock_now.return_value = tzdt(2015, 8, 17, 23, 0)
            expected = tzdt(2015, 8, 19, 19, 0)
            self.assertEqual(t.next(), expected)

            # now: 8/18 at 9am, expected next is 8/19 at 7pm
            mock_now.return_value = tzdt(2015, 8, 18, 9, 0)
            expected = tzdt(2015, 8, 19, 19, 0)
            self.assertEqual(t.next(), expected)

            # now: 8/19 at 9am, expected next is 8/19 at 7pm
            mock_now.return_value = tzdt(2015, 8, 19, 9, 0)
            expected = tzdt(2015, 8, 19, 19, 0)
            self.assertEqual(t.next(), expected)

            # now: 2015-8-19 at 10pm, expected next is 8/20 at 7pm
            mock_now.return_value = tzdt(2015, 8, 19, 22, 0)
            expected = tzdt(2015, 8, 20, 19, 0)
            self.assertEqual(t.next(), expected)

            # now: 2015-8-20 at 10am, expected next is 8/20 at 7pm
            mock_now.return_value = tzdt(2015, 8, 20, 10, 0)
            expected = tzdt(2015, 8, 20, 19, 0)
            self.assertEqual(t.next(), expected)

            # now: 2015-8-20 at 10pm, we're done
            mock_now.return_value = tzdt(2015, 8, 20, 22, 0)
            self.assertIsNone(t.next())

        # Clean up
        t.delete()

    def test_next_with_multiple_rules(self):
        """Test `next` when we have multiple RRULE requirements."""

        # Every Monday. Then every Tuesday until 8/15/2015 (sat)
        rrule = (
            'RRULE:FREQ=WEEKLY;BYDAY=MO\n'
            'RRULE:FREQ=WEEKLY;UNTIL=20150815T050000Z;BYDAY=TU'
        )
        t = Trigger.objects.create(
            name="x",
            time=time(9, 0),  # 9am
            trigger_date=date(2015, 8, 1),
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: Sat 08/8 at 11:00am, expected: next is Mon 8/10
            mock_now.return_value = tzdt(2015, 8, 8, 11, 0)
            expected = tzdt(2015, 8, 10, 9, 0)
            self.assertEqual(t.next(), expected)

            # now: Mon 8/10 at 11:00am, expected next is Tues 8/11
            mock_now.return_value = tzdt(2015, 8, 10, 11, 0)
            expected = tzdt(2015, 8, 11, 9, 0)
            self.assertEqual(t.next(), expected)

            # now: Wed 8/12 at 11:00am, expected next is Mon 8/17
            mock_now.return_value = tzdt(2015, 8, 12, 11, 0)
            expected = tzdt(2015, 8, 17, 9, 0)
            self.assertEqual(t.next(), expected)

            # now: Mon 8/17 at 11am, expected next is Mon 24 (skipped Tues)
            mock_now.return_value = tzdt(2015, 8, 17, 11, 0)
            expected = tzdt(2015, 8, 24, 9, 0)

        # Clean up
        t.delete()

    def test_next_with_recurrence_and_time_of_day(self):
        """Test the value of `next` for triggers that have ONLY a `time_of_day`
        and `recurrences` set of days."""

        # 7pm on M, W, Th on Aug 17, 19, 20  (repeat until 8/21/2015)
        rrule = 'RRULE:FREQ=DAILY'
        t = Trigger.objects.create(
            name="x",
            time_of_day='early',
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 08/15 at 11:00am, expected: next is Mon 8/16
            mock_now.return_value = tzdt(2015, 8, 15, 11, 0)

            result = t.next()
            self.assertIsNotNone(result)
            self.assertEqual(result.day, 16)
            self.assertIn(result.hour, [6, 7, 8])

            # now: 08/15 at 4:00am, expected: next is Mon 8/15
            mock_now.return_value = tzdt(2015, 8, 15, 4, 0)
            result = t.next()
            self.assertIsNotNone(result)
            self.assertEqual(result.day, 15)
            self.assertIn(result.hour, [6, 7, 8])

        # Clean up
        t.delete()

    def test_default_trigger_timezone(self):
        """A Default trigger, with no user input should return UTC time"""
        trigger = Trigger.objects.create(
            name="Test Default",
            time=time(23, 59),
            recurrences='RRULE:FREQ=DAILY'
        )

        expected = datetime.combine(timezone.now(), time(23, 59))
        expected = timezone.make_aware(expected, timezone=timezone.utc)
        result = trigger.next()
        self.assertEqual(result.strftime("%c %z"), expected.strftime("%c %z"))

    def test_default_trigger_with_user_timezone(self):
        user = User.objects.create_user('u', 'u@example.com', 'pass')
        user.userprofile.timezone = 'America/Chicago'
        user.userprofile.save()

        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 2, 11, 30)
            trigger = Trigger.objects.create(
                name="Test Default",
                time=time(23, 59),
                recurrences='RRULE:FREQ=DAILY'
            )

            tz = pytz.timezone('America/Chicago')
            expected = tzdt(2015, 1, 2, 23, 59, tz=tz)
            result = trigger.next(user=user)
            self.assertEqual(result.strftime("%c %z"), expected.strftime("%c %z"))

    def test_custom_trigger_timezone(self):
        user = User.objects.create_user('u', 'u@example.com', 'pass')
        user.userprofile.timezone = 'America/Chicago'
        user.userprofile.save()

        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 2, 11, 30)

            trigger = Trigger.objects.create(
                user=user,
                name="User Custom Trigger",
                time=time(23, 59),
                recurrences='RRULE:FREQ=DAILY'
            )

            tz = pytz.timezone('America/Chicago')
            expected = tzdt(2015, 1, 2, 23, 59, tz=tz)
            result = trigger.next()  # When called with no extra input.
            self.assertEqual(result.strftime("%c %z"), expected.strftime("%c %z"))

            result = trigger.next(user=user)  # When called with input.
            self.assertEqual(result.strftime("%c %z"), expected.strftime("%c %z"))

    def test_create_relative_reminder(self):
        """Creating a UserAction with a default relative reminder trigger should
        result in a new custom trigger with pre-filled data."""
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)
        beh = mommy.make(Behavior, title="Beh", state="published")
        beh.goals.add(goal)
        act = mommy.make(Action, behavior=beh, title='Act', state='published')

        default = Trigger.objects.create(
            name="Default", time=time(13, 30), recurrences="RRULE:FREQ=DAILY",
            relative_value=1, relative_units="weeks"
        )
        act.default_trigger = default
        act.save()

        user = User.objects.create_user("un", "em@il.com", 'pass')
        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 1, 11, 45)
            ua = UserAction.objects.create(user=user, action=act)
            # A custom trigger should have been created
            self.assertIsNotNone(ua.custom_trigger)
            self.assertEqual(ua.default_trigger, default)
            self.assertNotEqual(ua.trigger, default)
            custom = ua.trigger

            # expected next trigger is a week later in the user's timezone
            tz = pytz.timezone(user.userprofile.timezone)
            expected = tzdt(2015, 1, 8, 13, 30, tz=tz)
            expected = expected.strftime("%c %z")
            actual = custom.next().strftime("%c %z")
            self.assertEqual(actual, expected)

    def test_create_relative_reminder_start_when_selected(self):
        """Creating a UserAction with a default `start_when_selected` trigger
        should result in a new custom trigger with pre-filled data."""
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)
        beh = mommy.make(Behavior, title="Beh", state="published")
        beh.goals.add(goal)
        act = mommy.make(Action, behavior=beh, title='Act', state='published')

        default = Trigger.objects.create(
            name="Default", time=time(13, 30), recurrences="RRULE:FREQ=DAILY",
            start_when_selected=True,
        )
        act.default_trigger = default
        act.save()

        user = User.objects.create_user("un", "em@il.com", 'pass')
        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 1, 11, 45)
            ua = UserAction.objects.create(user=user, action=act)
            # A custom trigger should have been created
            self.assertIsNotNone(ua.custom_trigger)
            self.assertEqual(ua.default_trigger, default)
            self.assertNotEqual(ua.trigger, default)
            custom = ua.trigger

            # expected next trigger should be the same date as the UserAction's
            # creation date, with the Trigger time + the user's timezone
            tz = pytz.timezone(user.userprofile.timezone)
            expected = tzdt(2015, 1, 1, 13, 30, tz=tz)
            expected = expected.strftime("%c %z")
            actual = custom.next().strftime("%c %z")
            self.assertEqual(actual, expected)

    def test_relative_reminder_start_when_selected_series(self):
        """Test a series of generated relative reminder times."""
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)
        beh = mommy.make(Behavior, title="Beh", state="published")
        beh.goals.add(goal)
        act = mommy.make(Action, behavior=beh, title='Act', state='published')

        default = Trigger.objects.create(
            name="RR-start upon selection",
            time=time(9, 0),
            recurrences="RRULE:FREQ=DAILY;INTERVAL=2;COUNT=2",
            start_when_selected=True,
        )
        act.default_trigger = default
        act.save()

        user = User.objects.create_user("un", "em@il.com", 'pass')
        custom_trigger = None
        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 1, 11, 45)
            ua = UserAction.objects.create(user=user, action=act)

            # A custom trigger should have been created
            self.assertIsNotNone(ua.custom_trigger)
            self.assertEqual(ua.default_trigger, default)
            self.assertNotEqual(ua.trigger, default)
            custom_trigger = ua.trigger

            # Get the user's timezone
            tz = pytz.timezone(user.userprofile.timezone)

            # Test some expected "next" values.
            # At Jan 1, 11:45, next should be Jan 1, 9:00
            expected = tzdt(2015, 1, 1, 9, 0, tz=tz).strftime("%c %z")
            actual = custom_trigger.next().strftime("%c %z")
            self.assertEqual(actual, expected)

            # On Jan 2, next should be Jan 3, 9:00
            mock_now.return_value = tzdt(2015, 1, 2, 12, 0)
            expected = tzdt(2015, 1, 3, 9, 0, tz=tz).strftime("%c %z")
            actual = custom_trigger.next().strftime("%c %z")
            self.assertEqual(actual, expected)

            # On Jan 3, 7:15, next should be Jan 3, 9:00
            mock_now.return_value = tzdt(2015, 1, 3, 7, 15)
            expected = tzdt(2015, 1, 3, 9, 0, tz=tz).strftime("%c %z")
            actual = custom_trigger.next().strftime("%c %z")
            self.assertEqual(actual, expected)

            # On Jan 3, 4pm, next should be None since COUNT=2
            mock_now.return_value = tzdt(2015, 1, 3, 16, 0)
            self.assertIsNone(custom_trigger.next())

    def test_relative_reminder_starts_on_appropriate_day(self):
        """Test that a relative reminder with a weekly recurrence actually
        starts on the appropriate day, and not just the very next day after
        it's selected."""

        # Weekly, Wed & Sun at 9am, for 4 occurences.
        default = Trigger.objects.create(
            name="RR-start upon selection",
            time=time(9, 0),
            recurrences="RRULE:FREQ=WEEKLY;COUNT=4;BYDAY=WE,SU",
            start_when_selected=True,
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 12, 1, 14, 30)  # 2:30pm Dec 1

            # Test some expected "next" values.
            # At Jan 1, 11:45, next should be Jan 1, 9:00
            expected = tzdt(2015, 12, 2, 9, 0, tz=timezone.utc).strftime("%c %z")
            actual = default.next().strftime("%c %z")
            self.assertEqual(actual, expected)

            # Test the occurences
            occurs = default.get_occurences()
            self.assertEqual(len(occurs), 4)
            actual = occurs[0].strftime("%c %z")
            self.assertEqual(actual, expected)

    def test_relative_reminder_daily_with_count(self):
        """A relative reminder that repeats daily for a set number of days"""

        t = Trigger.objects.create(
            name="Daily with Count",
            time=time(12, 0),
            trigger_date=date(2016, 1, 4),  # Monday, Jan 4
            recurrences='RRULE:FREQ=DAILY;COUNT=3',  # Repeats 3 times
            start_when_selected=True,
            stop_on_complete=True,
            relative_value=1,  # NOTE: 1 day after selected.
            relative_units='days',
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # Day of selection: Sat Jan 2, 2016
            selection_date = tzdt(2016, 1, 2, 14, 30)
            mock_now.return_value = tzdt(2016, 1, 2, 14, 30)
            t.trigger_date = selection_date + timedelta(days=1)  # 1 day later
            t.save()

            # Now selection should start the next day, Jan 3
            expected = tzdt(2016, 1, 3, 12, 0)
            self.assertEqual(t.next(), expected)

            # That afternoon, we expect another on the next day
            mock_now.return_value = tzdt(2016, 1, 3, 20, 22)
            expected = tzdt(2016, 1, 4, 12, 0)
            self.assertEqual(t.next(), expected)

            # Jan 5 (day 3 after selection) in the morning
            mock_now.return_value = tzdt(2016, 1, 5, 9, 0)
            expected = tzdt(2016, 1, 5, 12, 0)
            self.assertEqual(t.next(), expected)

            # in the afternoon, we should be done.
            mock_now.return_value = tzdt(2016, 1, 5, 13, 0)
            self.assertIsNone(t.next())

        t.delete()  # Clean up


class TestBehavior(TestCase):
    """Tests for the `Behavior` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(title="Test Goal")
        self.goal.categories.add(self.category)
        self.behavior = Behavior.objects.create(
            title='Test Behavior',
        )
        self.behavior.goals.add(self.goal)

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test__str__(self):
        expected = "Test Behavior"
        actual = "{}".format(self.behavior)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        behavior = Behavior.objects.create(title="New Name")
        behavior.save()
        self.assertEqual(behavior.title_slug, "new-name")

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        b = Behavior(title="New")
        b.save(created_by=u)
        self.assertEqual(b.created_by, u)
        u.delete()  # Clean up
        b.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.behavior.save(updated_by=u)
        self.assertEqual(self.behavior.updated_by, u)
        u.delete()  # Clean up

    def test_get_absolute_url(self):
        self.assertEqual(
            self.behavior.get_absolute_url(),
            "/goals/behaviors/{0}-test-behavior/".format(self.behavior.id)


        )

    def test_get_update_url(self):
        self.assertEqual(
            self.behavior.get_update_url(),
            "/goals/behaviors/{0}-test-behavior/update/".format(self.behavior.id)

        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.behavior.get_delete_url(),
            "/goals/behaviors/{0}-test-behavior/delete/".format(self.behavior.id)

        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.behavior.state, "draft")

    def test_review(self):
        self.behavior.review()  # Switch to pending-review
        self.assertEqual(self.behavior.state, "pending-review")

    def test_decline(self):
        self.behavior.review()  # Switch to pending-review
        self.behavior.decline()  # then decline
        self.assertEqual(self.behavior.state, "declined")

    def test_publish(self):
        self.behavior.review()  # Switch to pending-review
        self.behavior.publish()  # then publish
        self.assertEqual(self.behavior.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.behavior.state, "draft")
        self.behavior.publish()  # then publish
        self.assertEqual(self.behavior.state, "published")

    def test_clean_title_on_save(self):
        self.behavior.title = "    A NEW title."
        self.behavior.save()
        self.assertEqual(self.behavior.title, "A NEW title")

    def test_clean_more_info_on_save(self):
        self.behavior.more_info = "    more.   "
        self.behavior.save()
        self.assertEqual(self.behavior.more_info, "more.")

    def test_clean_description_on_save(self):
        self.behavior.description = "  more descriptions.   "
        self.behavior.save()
        self.assertEqual(self.behavior.description, "more descriptions.")


class TestAction(TestCase):
    """Tests for the `Action` model."""

    @classmethod
    def setUpTestData(cls):
        pub = 'published'
        cls.cat = mommy.make(Category, title="Cat", state=pub)
        cls.goal = mommy.make(Goal, title="Goal", state=pub)
        cls.goal.categories.add(cls.cat)

    def setUp(self):
        self.behavior = mommy.make(Behavior, title='Test Behavior')
        self.action = mommy.make(
            Action, behavior=self.behavior, title="Test Action"
        )

    def tearDown(self):
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()

    def test_next_bucket(self):
        # When the method is provided a bucket name.
        self.assertEqual(Action.next_bucket(Action.PREP), Action.CORE)
        self.assertEqual(Action.next_bucket(Action.CORE), Action.CHECKUP)
        self.assertEqual(Action.next_bucket(Action.HELPER), Action.CHECKUP)
        self.assertEqual(Action.next_bucket(Action.CHECKUP), None)
        self.assertEqual(Action.next_bucket(None), Action.PREP)

        # When the method is provided a dict of bucket progress
        data = {
            Action.PREP: False,
            Action.CORE: False,
            Action.HELPER: False,
            Action.CHECKUP: False
        }
        self.assertEqual(Action.next_bucket(data), Action.PREP)

        data[Action.PREP] = True
        self.assertEqual(Action.next_bucket(data), Action.CORE)

        data[Action.CORE] = True
        self.assertEqual(Action.next_bucket(data), Action.CHECKUP)

        data[Action.HELPER] = True
        self.assertEqual(Action.next_bucket(data), Action.CHECKUP)

        data[Action.CHECKUP] = True
        self.assertEqual(Action.next_bucket(data), None)

    def test__set_bucket(self):
        """Ensure that _set_bucket puts an action in the correct bucket"""
        action = Action(self.behavior, title='BUCKET-TEST')
        for action_type, bucket in Action.BUCKET_MAPPING.items():
            action.action_type = action_type
            action._set_bucket()
            self.assertEqual(action.bucket, bucket)

    def test__str__(self):
        expected = "Test Action"
        actual = "{}".format(self.action)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        action = Action.objects.create(behavior=self.behavior, title="New Name")
        action.save()
        self.assertEqual(action.title_slug, "new-name")

    def test_is_helper(self):
        self.assertFalse(self.action.is_helper)  # default is core.

        self.action.action_type = Action.REINFORCING
        self.assertFalse(self.action.is_helper)

        self.action.action_type = Action.ENABLING
        self.assertFalse(self.action.is_helper)

        self.action.action_type = Action.SHOWING
        self.assertFalse(self.action.is_helper)

        self.action.action_type = Action.ASKING
        self.assertFalse(self.action.is_helper)

        # Test the Helpers...
        for at in Action.HELPERS:
            self.action.action_type = at
            self.assertTrue(self.action.is_helper)

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        a = Action(title="New", behavior=self.behavior)
        a.save(created_by=u)
        self.assertEqual(a.created_by, u)
        u.delete()  # Clean up
        a.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.action.save(updated_by=u)
        self.assertEqual(self.action.updated_by, u)
        u.delete()  # Clean up

    def test_get_absolute_url(self):
        self.assertEqual(
            self.action.get_absolute_url(),
            "/goals/actions/{0}-test-action/".format(self.action.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.action.get_update_url(),
            "/goals/actions/{0}-test-action/update/".format(self.action.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.action.get_delete_url(),
            "/goals/actions/{0}-test-action/delete/".format(self.action.id)
        )

    def test_create_action_classmethod_urls(self):
        """Ensure the auto-magically created classmethod urls work."""
        for action_type in Action.BUCKET_MAPPING.keys():
            meth = 'get_create_{}_action_url'.format(action_type)
            url = getattr(Action, meth)()
            expected = '/goals/new/action/?actiontype={}'.format(action_type)
            self.assertEqual(url, expected)

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.action.state, "draft")

    def test_review(self):
        self.action.review()  # Switch to pending-review
        self.assertEqual(self.action.state, "pending-review")

    def test_decline(self):
        self.action.review()  # Switch to pending-review
        self.action.decline()  # then decline
        self.assertEqual(self.action.state, "declined")

    def test_publish(self):
        self.action.review()  # Switch to pending-review
        self.action.publish()  # then publish
        self.assertEqual(self.action.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.action.state, "draft")
        self.action.publish()  # then publish
        self.assertEqual(self.action.state, "published")

    def test_clean_title_on_save(self):
        self.action.title = "    A NEW title."
        self.action.save()
        self.assertEqual(self.action.title, "A NEW title")

    def test_clean_more_info_on_save(self):
        self.action.more_info = "    more.   "
        self.action.save()
        self.assertEqual(self.action.more_info, "more.")

    def test_clean_description_on_save(self):
        self.action.description = "  more descriptions.   "
        self.action.save()
        self.assertEqual(self.action.description, "more descriptions.")

    def test_clean_notification_on_save(self):
        self.action.notification_text = " Here's a\nnotification   "
        self.action.save()
        self.assertEqual(
            self.action.notification_text,
            "Here's a notification."
        )

    def test_get_notification_title(self):
        goal = Mock(title='Pass tests')
        self.assertEqual(
            self.action.get_notification_title(goal),
            goal.title
        )

    def test_get_notification_text(self):
        self.action.notification_text = "You can read this."
        self.assertEqual(
            self.action.get_notification_text(),
            self.action.notification_text
        )


class TestUserGoal(TestCase):
    """Tests for the `UserGoal` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.goal = Goal.objects.create(
            title='Test Goal',
            subtitle="Test Subtitle",

        )
        self.ug = UserGoal.objects.create(
            user=self.user,
            goal=self.goal
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        UserGoal.objects.filter(id=self.ug.id).delete()

    def test__str__(self):
        expected = "Test Goal"
        actual = "{}".format(self.ug)
        self.assertEqual(expected, actual)

    def test_progress_value(self):
        # we haven't created any GoalProgress data, so this should be zero
        self.assertEqual(self.ug.progress_value, 0.0)

    def test_custom_triggers_allowed(self):
        """Ensure that custom triggers are allowed when the user is not
        enrolled in any packages (the default)."""
        self.assertEqual(self.user.packageenrollment_set.count(), 0)
        self.assertTrue(self.ug.custom_triggers_allowed)

    def test_custom_triggers_not_allowed(self):
        """Ensure that custom triggers are not allowed when the user is
        enrolled in a package that restricts this feature."""
        cat = Category.objects.create(order=1, title="PE Cat")
        admin = User.objects.create_superuser('x', 'x@y.z', '-')
        pe = PackageEnrollment.objects.create(
            user=self.user,
            category=cat,
            prevent_custom_triggers=True,
            enrolled_by=admin
        )
        pe.goals.add(self.goal)

        self.assertEqual(self.user.packageenrollment_set.count(), 1)
        self.assertFalse(self.ug.custom_triggers_allowed)
        cat.delete()
        admin.delete()


class TestUserBehavior(TestCase):
    """Tests for the `UserBehavior` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.goal = Goal.objects.create(title="Goal for Behavior")
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.behavior.goals.add(self.goal)
        self.ub = UserBehavior.objects.create(
            user=self.user,
            behavior=self.behavior
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        UserBehavior.objects.filter(id=self.ub.id).delete()

    def test__str__(self):
        expected = "Test Behavior"
        actual = "{}".format(self.ub)
        self.assertEqual(expected, actual)

    def test_custom_triggers_allowed(self):
        """Ensure that custom triggers are allowed when the user is not
        enrolled in any packages (the default)."""
        self.assertEqual(self.user.packageenrollment_set.count(), 0)
        self.assertTrue(self.ub.custom_triggers_allowed)

    def test_custom_triggers_not_allowed(self):
        """Ensure that custom triggers are not allowed when the user is
        enrolled in a package that restricts this feature."""
        cat = Category.objects.create(order=1, title="PE Cat")
        admin = User.objects.create_superuser('x', 'x@y.z', '-')
        pe = PackageEnrollment.objects.create(
            user=self.user,
            category=cat,
            prevent_custom_triggers=True,
            enrolled_by=admin
        )
        pe.goals.add(self.goal)

        self.assertEqual(self.user.packageenrollment_set.count(), 1)
        self.assertFalse(self.ub.custom_triggers_allowed)
        cat.delete()
        admin.delete()


class TestUserAction(TestCaseDates):
    """Tests for the `UserAction` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.goal = Goal.objects.create(title="Goal for Behavior", state='published')
        self.ug = UserGoal.objects.create(user=self.user, goal=self.goal)
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.behavior.goals.add(self.goal)
        self.ub = UserBehavior.objects.create(
            user=self.user,
            behavior=self.behavior
        )
        self.action = Action.objects.create(
            title='Test Action',
            behavior=self.behavior
        )
        self.ua = UserAction.objects.create(
            user=self.user,
            action=self.action
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()
        UserAction.objects.filter(id=self.ua.id).delete()

    def test__str__(self):
        expected = "Test Action"
        actual = "{}".format(self.ua)
        self.assertEqual(expected, actual)

    def test__completed(self):
        # When we have no UserCompletedActions
        self.assertFalse(self.ua._completed('-').exists())

        # We we have 1 UserCompletedAction
        kwargs = {'useraction': self.ua, 'user': self.user, 'action': self.action}
        uca = mommy.make(UserCompletedAction, **kwargs)
        self.assertTrue(self.ua._completed('-').exists())
        uca.delete()

    def test_num_completed(self):
        # When we have no UserCompletedActions
        self.assertEqual(self.ua.num_completed, 0)

        # We we have 1 UserCompletedAction
        kwargs = {
            'useraction': self.ua,
            'user': self.user,
            'action': self.action,
            'state': 'completed',
        }
        uca = mommy.make(UserCompletedAction, **kwargs)
        self.assertEqual(self.ua.num_completed, 1)
        uca.delete()

    def test_num_uncompleted(self):
        # When we have no UserCompletedActions
        self.assertEqual(self.ua.num_uncompleted, 0)

        # We we have 1 UserCompletedAction
        kwargs = {
            'useraction': self.ua,
            'user': self.user,
            'action': self.action,
            'state': 'uncompleted',
        }
        uca = mommy.make(UserCompletedAction, **kwargs)
        self.assertEqual(self.ua.num_uncompleted, 1)
        uca.delete()

    def test_num_snoozed(self):
        # When we have no UserCompletedActions
        self.assertEqual(self.ua.num_snoozed, 0)

        # We we have 1 UserCompletedAction
        kwargs = {
            'useraction': self.ua,
            'user': self.user,
            'action': self.action,
            'state': 'snoozed',
        }
        uca = mommy.make(UserCompletedAction, **kwargs)
        self.assertEqual(self.ua.num_snoozed, 1)
        uca.delete()

    def test_num_dismissed(self):
        # When we have no UserCompletedActions
        self.assertEqual(self.ua.num_dismissed, 0)

        # We we have 1 UserCompletedAction
        kwargs = {
            'useraction': self.ua,
            'user': self.user,
            'action': self.action,
            'state': 'dismissed',
        }
        uca = mommy.make(UserCompletedAction, **kwargs)
        self.assertEqual(self.ua.num_dismissed, 1)
        uca.delete()

    def test_completed_today(self):
        # ensure that the action is completed, and this should return True
        UserCompletedAction.objects.create(
            user=self.user,
            action=self.action,
            useraction=self.ua,
            state="completed"
        )
        self.assertTrue(self.ua.completed_today)

    def test_completed_today_incomplete(self):
        # When the user has not completed the action, this should return False.
        self.assertFalse(self.ua.completed_today)

    def test_user_behavior(self):
        self.assertEqual(self.ua.user_behavior, self.ub)

    def test_get_user_goals(self):
        self.assertEqual(
            list(self.ua.get_user_goals()),
            list(self.ub.get_user_goals())
        )

    def test_get_primary_goal(self):
        # When the `primary_goal` field is null, return the first of the
        # user's goals based on the action's parent behavior
        self.assertIsNone(self.ua.primary_goal)
        self.assertEqual(self.ua.get_primary_goal(), self.goal)

        # When we *do* have a primary goal, this method should return it.
        primary_goal = Goal.objects.create(title="Primary")
        self.ua.primary_goal = primary_goal
        self.ua.save()

        self.assertIsNotNone(self.ua.primary_goal)
        self.assertEqual(self.ua.get_primary_goal(), primary_goal)

        # Clean up
        Goal.objects.filter(title="Primary").delete()

    def test_custom_triggers_allowed(self):
        """Ensure that custom triggers are allowed when the user is not
        enrolled in any packages (the default)."""
        self.assertEqual(self.user.packageenrollment_set.count(), 0)
        self.assertTrue(self.ua.custom_triggers_allowed)

    def test_custom_triggers_not_allowed(self):
        """Ensure that custom triggers are not allowed when the user is
        enrolled in a package that restricts this feature."""
        cat = Category.objects.create(order=1, title="PE Cat")
        admin = User.objects.create_superuser('x', 'x@y.z', '-')
        pe = PackageEnrollment.objects.create(
            user=self.user,
            category=cat,
            prevent_custom_triggers=True,
            enrolled_by=admin
        )
        pe.goals.add(self.goal)

        self.assertEqual(self.user.packageenrollment_set.count(), 1)
        self.assertFalse(self.ua.custom_triggers_allowed)
        cat.delete()
        admin.delete()

    def test__set_next_trigger_date_when_no_trigger(self):
        # The action doesn't have a trigger, and there's no custom trigger,
        # calling this essentially has no side effect
        self.assertIsNone(self.ua.next_trigger_date)
        self.assertIsNone(self.ua.prev_trigger_date)
        self.ua._set_next_trigger_date()
        self.assertIsNone(self.ua.next_trigger_date)
        self.assertIsNone(self.ua.prev_trigger_date)

    @patch.object(UserAction, 'default_trigger')
    def test__set_next_trigger_date_with_default_trigger(self, mock_trigger):
        prev_date = tzdt(2015, 10, 8, 11, 30)
        mock_trigger.previous.return_value = prev_date

        # Calling this the first time when both values are null...
        mock_trigger.next.return_value = tzdt(2015, 10, 9, 11, 30)
        self.ua.next = mock_trigger.next

        mock_trigger.is_relative = False

        self.assertIsNone(self.ua.next_trigger_date)
        self.assertIsNone(self.ua.prev_trigger_date)
        self.ua._set_next_trigger_date()
        self.assertEqual(self.ua.next_trigger_date, tzdt(2015, 10, 9, 11, 30))
        self.assertEqual(self.ua.prev_trigger_date, prev_date)

        # Calling this a second time should change the prev_trigger_date
        mock_trigger.reset_mock()
        mock_trigger.next.return_value = tzdt(2015, 10, 10, 11, 30)  # next day
        self.ua.next = mock_trigger.next

        self.ua._set_next_trigger_date()
        self.assertEqual(self.ua.next_trigger_date, tzdt(2015, 10, 10, 11, 30))
        self.assertEqual(self.ua.prev_trigger_date, tzdt(2015, 10, 9, 11, 30))

    @patch.object(UserAction, 'custom_trigger')
    def test__set_next_trigger_date_with_custom_trigger(self, mock_trigger):
        # Set some initial values for the next/prev trigger fields.
        self.ua.prev_trigger_date = tzdt(2015, 10, 8, 11, 30)
        self.ua.next_trigger_date = tzdt(2015, 10, 9, 11, 30)

        mock_trigger.next.return_value = tzdt(2015, 10, 10, 11, 30)
        self.ua.next = mock_trigger.next
        self.ua._set_next_trigger_date()

        # both next/prev dates should have gotten updated.
        self.assertEqual(self.ua.next_trigger_date, tzdt(2015, 10, 10, 11, 30))
        self.assertEqual(self.ua.prev_trigger_date, tzdt(2015, 10, 9, 11, 30))

        # Calling again should NOT change anything.
        self.ua._set_next_trigger_date()
        self.assertEqual(self.ua.next_trigger_date, tzdt(2015, 10, 10, 11, 30))
        self.assertEqual(self.ua.prev_trigger_date, tzdt(2015, 10, 9, 11, 30))

    @patch.object(UserAction, 'custom_trigger')
    def test__set_next_trigger_date_when_next_is_none(self, mock_trigger):
        # A non-None prev_trigger_date should not get overwritten by a None value.

        # Set some initial values for the next/prev trigger fields.
        self.ua.prev_trigger_date = tzdt(2015, 10, 8, 11, 30)
        self.ua.next_trigger_date = None
        mock_trigger.next.return_value = tzdt(2015, 10, 10, 11, 30)
        self.ua.next = mock_trigger.next

        self.ua._set_next_trigger_date()

        # Next should have gotten updated, but prev should stay the same
        self.assertEqual(self.ua.next_trigger_date, tzdt(2015, 10, 10, 11, 30))
        self.assertEqual(self.ua.prev_trigger_date, tzdt(2015, 10, 8, 11, 30))

        # Calling again should NOT change anything.
        self.ua._set_next_trigger_date()
        self.assertEqual(self.ua.next_trigger_date, tzdt(2015, 10, 10, 11, 30))
        self.assertEqual(self.ua.prev_trigger_date, tzdt(2015, 10, 8, 11, 30))

    def test_create_parent_user_behavior(self):
        """If a user somehow adds an Action without adding that Action's parent
        Behavior, the `create_parent_user_behavior` signal handler should
        create it."""
        b = Behavior.objects.create(title="Other", state="published")
        b.goals.add(self.goal)
        a = Action.objects.create(title="Do Other", behavior=b, state="published")

        # Ensure user does not have the behavior selected
        params = {'user': self.user, 'behavior': b}
        self.assertFalse(UserBehavior.objects.filter(**params).exists())

        # Add the action, and the behavior gets added too
        UserAction.objects.create(user=self.user, action=a)
        self.assertTrue(UserBehavior.objects.filter(**params).exists())

        # Clean up
        UserBehavior.objects.filter(behavior=b).delete()
        UserAction.objects.filter(action=a).delete()
        a.delete()
        b.delete()

    def test_relative_reminder_daily_with_count_until_stopped(self):
        """A relative reminder that repeats daily for a set number of days, but
        should stop when completed."""

        # Create a user in UTC so it's easier to think about the times below,
        # because triggers will always be in the user's local timezone
        user = User.objects.create(username="utc", email="u@t.c")
        profile = user.userprofile
        profile.timezone = 'UTC'
        profile.save()

        default = Trigger.objects.create(
            name="Daily with Count",
            time=time(12, 0),
            trigger_date=date(2016, 1, 1),
            recurrences='RRULE:FREQ=DAILY;COUNT=3',  # Repeats 3 times
            start_when_selected=True,  # starts when selected,
            stop_on_complete=True,  # stops when completed.
            relative_value=1,  # NOTE: 1 day after selected.
            relative_units='days',
        )
        action = Action.objects.create(title='NEW', behavior=self.behavior)
        action.default_trigger = default
        action.save()

        #     January 2016
        # Mo Tu We Th Fr Sa Su
        #              1  2  3
        #  4  5  6  7  8  9 10
        # 11 12 13 14 15 16 17
        # 18 19 20 21 22 23 24
        # 25 26 27 28 29 30 31

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # Day of selection: Mon, Jan 4 -- 9am
            selection_date = tzdt(2016, 1, 4, 9, 0)
            mock_now.return_value = selection_date

            # When the UserAction is created, the custom trigger gets created
            # from the `create_relative_reminder` signal handler.
            ua = UserAction.objects.create(user=user, action=action)

            # Check some initial values
            self.assertIsNotNone(ua.custom_trigger)
            self.assertEqual(
                ua.custom_trigger.trigger_date.strftime("%Y-%m-%d"),
                "2016-01-05"  # XXX 1 day after
            )

            # 1st notification, Jan 5
            mock_now.return_value = tzdt(2016, 1, 5, 9, 0)
            expected = tzdt(2016, 1, 5, 12, 0)
            self.assertDatetimesEqual(ua.next(), expected)
            # after noon, at 1pm
            mock_now.return_value = tzdt(2016, 1, 5, 13, 0)
            expected = tzdt(2016, 1, 6, 12, 0)
            self.assertDatetimesEqual(ua.next(), expected)

            # 2nd notification Jan 6
            mock_now.return_value = tzdt(2016, 1, 6, 9, 0)
            expected = tzdt(2016, 1, 6, 12, 0)
            self.assertDatetimesEqual(ua.next(), expected)
            # after noon, at 1pm
            mock_now.return_value = tzdt(2016, 1, 6, 13, 0)
            expected = tzdt(2016, 1, 7, 12, 0)
            self.assertDatetimesEqual(ua.next(), expected)

            # 3rd notification Jan 7
            mock_now.return_value = tzdt(2016, 1, 7, 9, 0)
            expected = tzdt(2016, 1, 7, 12, 0)
            self.assertDatetimesEqual(ua.next(), expected)
            # after noon, at 1pm
            mock_now.return_value = tzdt(2016, 1, 7, 13, 0)
            self.assertIsNone(ua.next())

            # Back up to early in Day 2 (Jan 6)
            mock_now.return_value = tzdt(2016, 1, 6, 9, 0)
            # Add a UserCompletedAction and see if it stops in the middle.
            UserCompletedAction.objects.create(
                user=user, useraction=ua, action=action, state="completed"
            )
            # That should stop any further notifications.
            self.assertIsNone(ua.next())

        # Clean up
        action.delete()
        default.delete()
        user.delete()

    def test_relative_reminder_daily_with_count_until_stopped_local(self):
        """A relative reminder that repeats daily for a set number of days, but
        should stop when completed."""

        # NOTE: triggers will always be in the user's local timezone
        user = User.objects.create(username="cst", email="c@s.t")
        profile = user.userprofile
        profile.timezone = 'America/Chicago'  # CST
        profile.save()
        tz = pytz.timezone(profile.timezone)

        default = Trigger.objects.create(
            name="Daily with Count",
            time=time(12, 0),
            trigger_date=date(2016, 1, 1),
            recurrences='RRULE:FREQ=DAILY;COUNT=3',  # Repeats 3 times
            start_when_selected=True,  # starts when selected,
            stop_on_complete=True,  # stops when completed.
            relative_value=1,  # NOTE: 1 day after selected.
            relative_units='days',
        )
        action = Action.objects.create(title='NEW', behavior=self.behavior)
        action.default_trigger = default
        action.save()

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # NOTE: the trigger is for noon == 6pm UTC
            # Day of selection: Mon, Jan 4 -- 9am CST / 3pm UTC
            selection_date = tzdt(2016, 1, 4, 9, 0)
            mock_now.return_value = selection_date

            # When the UserAction is created, the custom trigger gets created
            # from the `create_relative_reminder` signal handler.
            ua = UserAction.objects.create(user=user, action=action)

            # Check some initial values
            self.assertIsNotNone(ua.custom_trigger)
            self.assertEqual(
                ua.custom_trigger.trigger_date.strftime("%Y-%m-%d"),
                "2016-01-05"  # XXX 1 day after
            )

            # 1st notification, Jan 5
            mock_now.return_value = tzdt(2016, 1, 5, 1, 0)
            expected = tzdt(2016, 1, 5, 12, 0, tz=tz)
            self.assertDatetimesEqual(ua.next(), expected)
            # after noon, at 1pm
            mock_now.return_value = tzdt(2016, 1, 5, 19, 0)
            expected = tzdt(2016, 1, 6, 12, 0, tz=tz)
            self.assertDatetimesEqual(ua.next(), expected)

            # 2nd notification Jan 6
            mock_now.return_value = tzdt(2016, 1, 6, 1, 0)
            expected = tzdt(2016, 1, 6, 12, 0, tz=tz)
            self.assertDatetimesEqual(ua.next(), expected)
            # after noon, at 1pm
            mock_now.return_value = tzdt(2016, 1, 6, 19, 0)
            expected = tzdt(2016, 1, 7, 12, 0, tz=tz)
            self.assertDatetimesEqual(ua.next(), expected)

            # 3rd notification Jan 7
            mock_now.return_value = tzdt(2016, 1, 7, 1, 0)
            expected = tzdt(2016, 1, 7, 12, 0, tz=tz)
            self.assertDatetimesEqual(ua.next(), expected)
            # after noon, at 1pm
            mock_now.return_value = tzdt(2016, 1, 7, 19, 0)
            self.assertIsNone(ua.next())

            # Back up to early in Day 2 (Jan 6)
            mock_now.return_value = tzdt(2016, 1, 6, 1, 0)
            # Add a UserCompletedAction and see if it stops in the middle.
            UserCompletedAction.objects.create(
                user=user, useraction=ua, action=action, state="completed"
            )
            # That should stop any further notifications.
            self.assertIsNone(ua.next())

        # Clean up
        action.delete()
        default.delete()
        user.delete()

    def test_queued_notifications(self):
        """UserAction.queued_notifications should return the right thing"""
        from notifications.models import GCMDevice, GCMMessage
        GCMDevice.objects.get_or_create(user=self.user, registration_id="x")

        # When there are no messages (should be the default)
        self.assertEqual(list(self.ua.queued_notifications()), [])

        # When there is a message
        # create(self, user, title, message, deliver_on, obj=None, content_type=None):
        msg = GCMMessage.objects.create(
            self.user,
            'test title',
            'test message',
            timezone.now(),
            obj=self.action,
        )
        self.assertEqual(self.ua.queued_notifications().count(), 1)

        # Clean up
        msg.delete()

    def test_enable_trigger_when_no_custom_trigger(self):
        """When there's no custom_trigger, this shouldn't do anything."""
        act = Action.objects.create(title="Foo", behavior=self.behavior)
        ua = UserAction.objects.create(user=self.user, action=act)
        self.assertIsNone(ua.custom_trigger)
        ua.enable_trigger()
        self.assertIsNone(ua.custom_trigger)

        # Clean up
        ua.delete()
        act.delete()

    def test_enable_trigger_when_custom_trigger(self):
        """When there IS a custom_trigger, this should set disabled=False."""
        act = Action.objects.create(title="Foo", behavior=self.behavior)
        ua = UserAction.objects.create(user=self.user, action=act)
        ua.custom_trigger = mommy.make(Trigger, user=self.user, disabled=True)

        self.assertTrue(ua.custom_trigger.disabled)
        ua.enable_trigger()
        self.assertFalse(ua.custom_trigger.disabled)

        # Clean up
        ua.delete()
        act.delete()

    def test_disable_trigger_when_no_custom_trigger_or_default_trigger(self):
        """When there's no custom_trigger OR default trigger, this shouldn't
        do anything."""
        act = Action.objects.create(title="Foo", behavior=self.behavior)
        ua = UserAction.objects.create(user=self.user, action=act)
        self.assertIsNone(ua.custom_trigger)
        ua.disable_trigger()
        self.assertIsNone(ua.custom_trigger)

        # Clean up
        ua.delete()
        act.delete()

    def test_disable_trigger_when_no_custom_trigger(self):
        """When there's no custom_trigger BUT there IS a default trigger, this
        should create one and disable it"""
        act = Action.objects.create(title="Foo", behavior=self.behavior)
        act.default_trigger = mommy.make(Trigger, disabled=False)
        ua = UserAction.objects.create(user=self.user, action=act)

        self.assertIsNone(ua.custom_trigger)
        ua.disable_trigger()
        self.assertTrue(ua.custom_trigger.disabled)

        # Clean up
        ua.delete()
        act.delete()

    def test_disable_trigger_when_custom_trigger(self):
        """When there IS a custom_trigger, this should set disabled=True."""
        act = Action.objects.create(title="Foo", behavior=self.behavior)
        ua = UserAction.objects.create(user=self.user, action=act)
        ua.custom_trigger = mommy.make(Trigger, disabled=False)

        self.assertFalse(ua.custom_trigger.disabled)
        ua.disable_trigger()
        self.assertTrue(ua.custom_trigger.disabled)

        # Clean up
        ua.delete()
        act.delete()


class TestUserCompletedAction(TestCase):
    """Tests for the `UserCompletedAction` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            title='Test Action',
            behavior=self.behavior
        )
        self.ua = UserAction.objects.create(
            user=self.user,
            action=self.action
        )

        # Default state == "-"
        self.uca = UserCompletedAction.objects.create(
            user=self.user,
            useraction=self.ua,
            action=self.action
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()
        UserAction.objects.filter(id=self.ua.id).delete()
        UserCompletedAction.objects.filter(id=self.uca.id).delete()

    def test__str__(self):
        expected = "{}".format(self.action.title)
        actual = "{}".format(self.uca)
        self.assertEqual(expected, actual)

    def test_uncompleted(self):
        self.assertFalse(self.uca.uncompleted)

        uca = UserCompletedAction.objects.create(
            user=self.user,
            useraction=self.ua,
            action=self.action,
            state=UserCompletedAction.UNCOMPLETED
        )
        self.assertTrue(uca.uncompleted)
        uca.delete()

    def test_completed(self):
        self.assertFalse(self.uca.completed)

    def test_dismissed(self):
        self.assertFalse(self.uca.dismissed)

    def test_snoozed(self):
        self.assertFalse(self.uca.snoozed)


class TestUserCategory(TestCase):
    """Tests for the `UserCategory` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.category = Category.objects.create(
            title='Test Category',
            order=1,
        )
        self.uc = UserCategory.objects.create(
            user=self.user,
            category=self.category
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Category.objects.filter(id=self.category.id).delete()
        UserCategory.objects.filter(id=self.uc.id).delete()

    def test__str__(self):
        expected = "Test Category"
        actual = "{}".format(self.uc)
        self.assertEqual(expected, actual)

    def test_custom_triggers_allowed(self):
        """Ensure custom triggers are allowed by default."""
        self.assertTrue(self.uc.custom_triggers_allowed)

    def test_custom_triggers_not_allowed(self):
        """Ensure that custom triggers are not allowed when the user is
        enrolled in a package that restricts this feature."""
        admin = User.objects.create_superuser('x', 'x@y.z', '-')
        pe = PackageEnrollment.objects.create(
            user=self.user,
            category=self.category,
            prevent_custom_triggers=True,
            enrolled_by=admin
        )
        self.assertEqual(self.user.packageenrollment_set.count(), 1)
        self.assertFalse(self.uc.custom_triggers_allowed)
        pe.delete()


class TestPackageEnrollment(TestCase):
    """Tests for the `PackageEnrollment` model."""

    @classmethod
    def setUpTestData(cls):
        cls.admin, created = User.objects.get_or_create(
            username="admin",
            email="admin@example.com"
        )
        cls.user, created = User.objects.get_or_create(
            username="test",
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        cls.category = Category.objects.create(
            order=1,
            title="Test Category",
            packaged_content=True,
        )
        cls.category.publish()
        cls.category.package_contributors.add(cls.admin)

        # create some child content
        cls.goal = Goal.objects.create(title="G", description="G.")
        cls.goal.publish()
        cls.goal.categories.add(cls.category)
        cls.behavior = Behavior.objects.create(title='B')
        cls.behavior.publish()
        cls.behavior.save()
        cls.behavior.goals.add(cls.goal)
        cls.action = Action.objects.create(behavior=cls.behavior, title="A")
        cls.action.publish()
        cls.action.save()

    def setUp(self):
        # Create an actual package enrollment.
        self.pe = PackageEnrollment.objects.create(
            user=self.user,
            category=self.category,
            enrolled_by=self.admin
        )
        self.pe.goals.add(self.goal)

    def tearDown(self):
        PackageEnrollment.objects.all().delete()
        for m in [UserCategory, UserGoal, UserBehavior, UserAction]:
            m.objects.all().delete()

    def test__str__(self):
        expected = "Test User enrolled on {}".format(self.pe.enrolled_on)
        actual = "{}".format(self.pe)
        self.assertEqual(expected, actual)

    def test_defaults(self):
        """Test the PackageEnrollment's default values."""
        self.assertFalse(self.pe.prevent_custom_triggers)
        self.assertFalse(self.pe.accepted)

    def test_properties(self):
        self.assertEqual(
            self.pe.rendered_consent_summary,
            self.category.rendered_consent_summary
        )
        self.assertEqual(
            self.pe.rendered_consent_more,
            self.category.rendered_consent_more
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.pe.get_absolute_url(),
            reverse('goals:package-detail', args=[self.pe.id])
        )

    def test_get_accept_url(self):
        self.assertEqual(
            self.pe.get_accept_url(),
            reverse('goals:accept-enrollment', args=[self.pe.id])
        )

    def test_accept(self):
        self.pe.create_user_mappings = Mock()
        self.assertFalse(self.pe.accepted)
        self.pe.accept()
        self.assertTrue(self.pe.accepted)
        self.pe.create_user_mappings.assert_called_once_with()

    def test_create_user_mappings(self):
        self.assertFalse(self.user.usercategory_set.exists())
        self.assertFalse(self.user.usergoal_set.exists())
        self.assertFalse(self.user.userbehavior_set.exists())
        self.assertFalse(self.user.useraction_set.exists())
        self.pe.create_user_mappings()
        self.assertTrue(self.user.usercategory_set.exists())
        self.assertTrue(self.user.usergoal_set.exists())
        self.assertTrue(self.user.userbehavior_set.exists())
        self.assertTrue(self.user.useraction_set.exists())


# -----------------------------------------------------------------------------
# User-created stuff; CustomGoal, CustomAction, CustomActionFeedback, etc
# -----------------------------------------------------------------------------


class TestCustomGoal(TestCase):
    """Tests for the `CustomGoal` model."""

    def setUp(self):
        self.user = mommy.make(User)
        self.customgoal = mommy.make(CustomGoal, title='test', user=self.user)

    def tearDown(self):
        CustomGoal.objects.filter(id=self.customgoal.id).delete()

    def test__str__(self):
        expected = self.customgoal.title
        actual = "{}".format(self.customgoal)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        customgoal = CustomGoal.objects.create(title="New CG", user=self.user)
        customgoal.save()
        self.assertEqual(customgoal.title_slug, "new-cg")
        customgoal.delete()  # Clean up.


class TestCustomAction(TestCase):
    """Tests for the `CustomAction` model."""

    def setUp(self):
        self.user = mommy.make(User)
        self.customgoal = mommy.make(CustomGoal, title='Goal', user=self.user)
        self.customaction = mommy.make(
            CustomAction,
            user=self.user,
            customgoal=self.customgoal,
            title="Action"
        )

    def test__str__(self):
        expected = self.customaction.title
        actual = "{}".format(self.customaction)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        customaction = CustomAction.objects.create(
            title="New CG",
            user=self.user,
            customgoal=self.customgoal
        )
        customaction.save()
        self.assertEqual(customaction.title_slug, "new-cg")
        customaction.delete()  # Clean up.

    def test_queued_notifications(self):
        """CustomAction.queued_notifications should return the right thing"""
        from notifications.models import GCMDevice, GCMMessage
        GCMDevice.objects.get_or_create(user=self.user, registration_id="x")

        # When there are no messages (should be the default)
        self.assertEqual(list(self.customaction.queued_notifications()), [])

        # When there is a message
        # create(self, user, title, message, deliver_on, obj=None, content_type=None):
        msg = GCMMessage.objects.create(
            self.user,
            'test title',
            'test message',
            timezone.now(),
            obj=self.customaction,
        )
        self.assertEqual(self.customaction.queued_notifications().count(), 1)

        # clean up
        msg.delete()

    # TODO: test trigger-related stuff


class TestUserCompletedCustomAction(TestCase):
    """Tests for the `UserCompletedCustomAction` model."""

    def setUp(self):
        self.user = mommy.make(User)
        self.customgoal = mommy.make(CustomGoal, title='Goal', user=self.user)
        self.customaction = mommy.make(
            CustomAction,
            user=self.user,
            customgoal=self.customgoal,
            title="Action"
        )
        self.ucca = mommy.make(
            UserCompletedCustomAction,
            user=self.user,
            customaction=self.customaction,
            customgoal=self.customgoal
        )

    def tearDown(self):
        UserCompletedCustomAction.objects.filter(id=self.ucca.id).delete()

    def test__str__(self):
        expected = self.customaction.title
        actual = "{}".format(self.ucca)
        self.assertEqual(expected, actual)

    def test_uncompleted(self):
        # state is unset
        self.assertFalse(self.ucca.uncompleted)

    def test_completed(self):
        # state is unset
        self.assertFalse(self.ucca.completed)

    def test_dismissed(self):
        # state is unset
        self.assertFalse(self.ucca.dismissed)

    def test_snoozed(self):
        # state is unset
        self.assertFalse(self.ucca.snoozed)


class TestCustomActionFeedback(TestCase):
    """Tests for the `CustomActionFeedback` model."""

    def setUp(self):
        self.user = mommy.make(User)
        self.customgoal = mommy.make(CustomGoal, title='Goal', user=self.user)
        self.customaction = mommy.make(
            CustomAction,
            user=self.user,
            customgoal=self.customgoal,
            title="Action"
        )
        self.caf = mommy.make(
            CustomActionFeedback,
            user=self.user,
            customaction=self.customaction,
            customgoal=self.customgoal
        )

    def tearDown(self):
        CustomActionFeedback.objects.filter(id=self.caf.id).delete()

    def test__str__(self):
        expected = self.customaction.title
        actual = "{}".format(self.caf)
        self.assertEqual(expected, actual)


class TestDailyProgress(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = mommy.make(User)
        cls.behavior = mommy.make(Behavior, id=1)

        status = {'behavior-1': 'TEST'}
        cls.progress = mommy.make(
            DailyProgress,
            user=cls.user,
            actions_total=4,
            actions_completed=1,
            actions_snoozed=2,
            actions_dismissed=1,
            customactions_total=1,
            customactions_completed=0,
            customactions_snoozed=0,
            customactions_dismissed=1,
            behaviors_total=1,
            behaviors_status=status,
        )

    def test_actions(self):
        expected = {
            'total': 4,
            'snoozed': 2,
            'completed': 1,
            'dismissed': 1,
        }
        self.assertDictEqual(self.progress.actions, expected)

    def test_customactions(self):
        expected = {
            'total': 1,
            'snoozed': 0,
            'completed': 0,
            'dismissed': 1,
        }
        self.assertDictEqual(self.progress.customactions, expected)

    def test_get_status_when_empty(self):
        """When there's no data, the get_status method should return the first
        bucket, as defined on Action.BUCKET_ORDER"""
        dp = DailyProgress()
        self.assertEqual(dp.get_status(self.behavior), Action.BUCKET_ORDER[0])

    def test_get_status(self):
        self.assertEqual(self.progress.get_status(self.behavior), 'TEST')

    def test_set_status(self):
        behavior = Mock(id=2)
        self.progress.set_status(behavior, 'FOO')
        self.assertEqual(self.progress.behaviors_status['behavior-2'], 'FOO')
