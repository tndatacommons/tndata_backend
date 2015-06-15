from datetime import time
from django.contrib.auth import get_user_model
from django.test import TestCase
from .. models import Trigger
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
        trigger = Trigger.objects.create_for_user(
            self.user,
            "New Trigger",
            time(8, 30),
            "RRULE:FREQ=WEEKLY;BYDAY=MO",
        )
        self.assertEqual(
            trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
