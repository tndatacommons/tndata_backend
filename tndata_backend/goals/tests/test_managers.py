from datetime import datetime, date, time
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .. models import Action, Behavior, Trigger, UserAction, UserBehavior
from .. settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_BEHAVIOR_TRIGGER_TIME,
    DEFAULT_BEHAVIOR_TRIGGER_RRULE,
)

User = get_user_model()


class TestTriggerManager(TestCase):
    """Tests for the `TriggerManager` manager."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("u", "u@a.com", "pass")

        cls.default_trigger = Trigger.objects.create(
            name="Default Trigger",
            trigger_type="time",
            time=time(12, 34),
            recurrences="RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        )

        cls.custom_trigger = Trigger.objects.create(
            user=cls.user,
            name="A Custom Trigger",
            trigger_type="time",
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
            date(2025, 3, 14),
            None
        )
        expected = datetime.combine(date(2025, 3, 14), time(9, 30))
        expected = timezone.make_aware(expected, timezone=timezone.utc)
        self.assertEqual(trigger.next(), expected)

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
