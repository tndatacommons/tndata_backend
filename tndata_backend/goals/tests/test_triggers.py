import pytz
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from model_mommy import mommy
from utils.user_utils import tzdt

from .. models import (
    Action,
    Category,
    Goal,
    Trigger,
    UserAction,
    UserCompletedAction,
)


class TestTrigger(TestCase):
    """Tests for the `Trigger` model."""

    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
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
        u = self.User.objects.create_user("get_tz_uer", "get_tz_user@example.com", "s")
        u.userprofile.timezone = "America/Chicago"
        t = Trigger.objects.create(
            user=u,
            name="self.User's test Trigger",
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

        trigger = mommy.make(
            Trigger,
            name="StopTrigger",
            time=time(17, 0),
            recurrences="RRULE:FREQ=DAILY",
            stop_on_complete=True,
        )
        act = mommy.make(
            Action,
            title='Act',
            state='published',
            default_trigger=trigger
        )
        act.goals.add(goal)

        user = mommy.make(self.User)
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
        act = mommy.make(Action, title='Act', state='published')
        act.goals.add(goal)

        user = mommy.make(self.User)
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
        trigger.user = mommy.make(self.User)
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
        trigger.user = mommy.make(self.User)
        trigger.save()
        self.assertIsNotNone(trigger.dynamic_trigger_date())
        trigger.delete()

    def test_dynamic_trigger_date_hours(self):
        """Ensure that this method returns the correct values for different
        time_of_day values based on the user's selected timezone."""

        user = mommy.make(self.User)
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
        self.assertEqual(hours, {18, 19, 20, 21})

        # Ensure late times are in [22, 23, 0, 1, 2]
        kwargs['time_of_day'] = 'late'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {22, 23, 0, 1, 2})

        # Ensure allday times are in [8, ... 17]
        kwargs['time_of_day'] = 'allday'
        trigger = mommy.make(Trigger, **kwargs)
        times = [trigger.dynamic_trigger_date(user=user) for i in range(100)]
        hours = set([t.hour for t in times])
        self.assertEqual(hours, {8, 9, 10, 11, 12, 13, 14, 15, 16, 17})

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

    def test_weekly_recurrences(self):
        """Test the value of `next` for recurrences that specify a distinct
        a weekly recurrence."""

        # Weekly until Sept 1, 2016 (starting Aug 1)
        rrule = 'RRULE:FREQ=WEEKLY;UNTIL=20160901T050000Z'
        t = Trigger.objects.create(
            time=time(13, 30),
            trigger_date=date(2016, 8, 1),  # Mon, 8/1/2016
            recurrences=rrule
        )

        with patch("goals.models.triggers.timezone.now") as mock_now:
            # now: 08/01 at 11:00am, expected: next is Mon 8/01, 1:30pm
            mock_now.return_value = tzdt(2016, 8, 1, 11, 0)
            expected = tzdt(2016, 8, 1, 13, 30)
            self.assertEqual(t.next(), expected)

            # now: Sun, 8/07 at 11:00am, expected next is 8/09 at 1:30pm
            mock_now.return_value = tzdt(2016, 8, 7, 11, 0)
            expected = tzdt(2016, 8, 8, 13, 30)
            self.assertEqual(t.next(), expected)

            # now: Sun, 8/14 at 11:00am, expected next is 8/15 at 1:30pm
            mock_now.return_value = tzdt(2016, 8, 14, 11, 0)
            expected = tzdt(2016, 8, 15, 13, 30)
            self.assertEqual(t.next(), expected)

            # now: Sat, 8/20 at 11:00am, expected next is 8/22 at 1:30pm
            mock_now.return_value = tzdt(2016, 8, 20, 11, 0)
            expected = tzdt(2016, 8, 22, 13, 30)
            self.assertEqual(t.next(), expected)

            # now: Thurs, 8/25 at 11:00am, expected next is 8/29 at 1:30pm
            mock_now.return_value = tzdt(2016, 8, 25, 11, 0)
            expected = tzdt(2016, 8, 29, 13, 30)
            self.assertEqual(t.next(), expected)

            # now: 8/30, we should be done.
            mock_now.return_value = tzdt(2016, 8, 30, 22, 0)
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
        user = self.User.objects.create_user('u', 'u@example.com', 'pass')
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
        user = self.User.objects.create_user('u', 'u@example.com', 'pass')
        user.userprofile.timezone = 'America/Chicago'
        user.userprofile.save()

        with patch("goals.models.triggers.timezone.now") as mock_now:
            mock_now.return_value = tzdt(2015, 1, 2, 11, 30)

            trigger = Trigger.objects.create(
                user=user,
                name="self.User Custom Trigger",
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
        act = mommy.make(Action, title='Act', state='published')
        act.goals.add(goal)

        default = Trigger.objects.create(
            name="Default", time=time(13, 30), recurrences="RRULE:FREQ=DAILY",
            relative_value=1, relative_units="weeks"
        )
        act.default_trigger = default
        act.save()

        user = self.User.objects.create_user("un", "em@il.com", 'pass')
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
        act = mommy.make(Action, title='Act', state='published')
        act.goals.add(goal)

        default = Trigger.objects.create(
            name="Default", time=time(13, 30), recurrences="RRULE:FREQ=DAILY",
            start_when_selected=True,
        )
        act.default_trigger = default
        act.save()

        user = self.User.objects.create_user("un", "em@il.com", 'pass')
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

    def test_change_to_relative_reminder_generates_custom_trigger(self):
        """If an Action's trigger is changed to relative or start_when_selected,
        this should generate a new custom Trigger for the user.

        1. A UserAction is a created, but only keeps it's default trigger (e.g
           in the case of a dynamic trigger.
        2. Its default trigger is then changed to be a relative or start when
           selected trigger.
        3. Saving the UserAction should generate a new custom trigger

        """
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)

        # Action with a dynamic default trigger
        act = mommy.make(Action, title='Act', state='published')
        act.goals.add(goal)

        default = Trigger.objects.create(
            name="Default", time_of_day="morning", frequency="daily"
        )
        act.default_trigger = default
        act.save()

        # Creating a UserAction, should *not* generate a custom trigger.
        user = self.User.objects.create_user("un", "em@il.com", 'pass')
        ua = UserAction.objects.create(user=user, action=act)
        self.assertIsNone(ua.custom_trigger)
        self.assertIsNotNone(ua.trigger)

        # Now, let's change that default trigger to be a relative reminder
        default.time_of_day = None
        default.frequency = None
        default.time = time(13, 30)
        default.recurrences = "RRULE:FREQ=DAILY"
        default.start_when_selected = True,
        default.relative_value = 1
        default.relative_units = "days"
        default.save()

        # A custom trigger should have been created
        ua.save()
        self.assertIsNotNone(ua.custom_trigger)
        self.assertIsNotNone(ua.custom_trigger.trigger_date)

        delta = ua.custom_trigger.trigger_date - ua.created_on
        self.assertEqual(delta.days, 1)

    def test_relative_reminder_start_when_selected_series(self):
        """Test a series of generated relative reminder times."""
        cat = mommy.make(Category, title="Cat", state='published')
        goal = mommy.make(Goal, title="Goa", state='published')
        goal.categories.add(cat)
        act = mommy.make(Action, title='Act', state='published')
        act.goals.add(goal)

        default = Trigger.objects.create(
            name="RR-start upon selection",
            time=time(9, 0),
            recurrences="RRULE:FREQ=DAILY;INTERVAL=2;COUNT=2",
            start_when_selected=True,
        )
        act.default_trigger = default
        act.save()

        user = self.User.objects.create_user("un", "em@il.com", 'pass')
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

    def test_recurrences_continue_afer_usercompletedactions_are_set(self):
        """A Trigger with a Recurrence should continue to get created for
        the life of that recurrence, _even_ after a user's got a "completed"
        UserCompletedAction."""
        user = self.User.objects.create_user('x', 'y@z.com', 'xxx')

        cat = mommy.make(Category, title="C", state="published")
        goal = mommy.make(Goal, title="G", state="published")
        goal.categories.add(cat)
        action = mommy.make(Action, title="A", state="published", sequence_order=0)
        action.goals.add(goal)

        trigger = Trigger.objects.create(
            user=user,
            time=time(13, 30),
            recurrences='RRULE:FREQ=DAILY',
            start_when_selected=True,
        )
        ua = mommy.make(UserAction, user=user, action=action, custom_trigger=trigger)
        ua.save()

        # Saving this should generate a trigger date (within the next 24 hours)
        self.assertIsNotNone(ua.next_trigger_date)

        # Should happen before tomorrow
        tomorrow = timezone.now() + timedelta(days=1)
        self.assertTrue(ua.next_trigger_date < tomorrow)

        # Even If we have *completed* an action, since this has a recurrence,
        # we should still get a next date.
        mommy.make(
            UserCompletedAction, user=user, action=action, useraction=ua,
            state=UserCompletedAction.COMPLETED
        )
        self.assertIsNotNone(ua.next())
        user.delete()

    def test_triggers_as_part_of_a_sequence(self):
        """A Trigger with a Recurrence should continue to get created for
        the life of that recurrence, _even_ after a user's got a "completed"
        UserCompletedAction."""
        user = self.User.objects.create_user('x', 'y@z.com', 'xxx')

        cat = mommy.make(Category, title="C", state="published")
        goal = mommy.make(Goal, title="G", state="published")
        goal.categories.add(cat)

        trigger_args = {
            'time': time(13, 30),
            'time_of_day': "allday",
            'frequency': "daily",
        }
        dt1 = Trigger.objects.create(**trigger_args)
        a1 = mommy.make(Action, title="A1", state="published",
                        sequence_order=1, default_trigger=dt1)
        a1.goals.add(goal)
        dt2 = Trigger.objects.create(**trigger_args)
        a2 = mommy.make(Action, title="A2", state="published",
                        sequence_order=2, default_trigger=dt2)
        a2.goals.add(goal)
        dt3 = Trigger.objects.create(**trigger_args)
        a3 = mommy.make(Action, title="A3", state="published",
                        sequence_order=3, default_trigger=dt3)
        a3.goals.add(goal)

        ua1 = mommy.make(UserAction, user=user, action=a1)
        ua2 = mommy.make(UserAction, user=user, action=a2)
        ua3 = mommy.make(UserAction, user=user, action=a3)

        # We shouldn't get next trigger dates until they the sequence is active
        for ua in [ua1, ua2, ua3]:
            ua.save(update_triggers=True)
        self.assertIsNotNone(ua1.next_trigger_date)
        self.assertIsNone(ua2.next_trigger_date)
        self.assertIsNone(ua3.next_trigger_date)

        # When we complete one, then the next in sequence should get queued.
        mommy.make(
            UserCompletedAction, user=user, action=a1, useraction=ua1,
            state=UserCompletedAction.COMPLETED
        )
        for ua in [ua1, ua2, ua3]:
            ua.save()
        self.assertIsNone(ua1.next_trigger_date)
        self.assertIsNotNone(ua2.next_trigger_date)
        self.assertIsNone(ua3.next_trigger_date)

        mommy.make(
            UserCompletedAction, user=user, action=a2, useraction=ua2,
            state=UserCompletedAction.COMPLETED
        )
        for ua in [ua1, ua2, ua3]:
            ua.save()
        self.assertIsNone(ua1.next_trigger_date)
        self.assertIsNone(ua2.next_trigger_date)
        self.assertIsNotNone(ua3.next_trigger_date)
