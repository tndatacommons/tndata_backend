import pytz
from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase

from .. models import Trigger
from .. serializers import CustomTriggerSerializer


User = get_user_model()


class TestCustomTriggerSerializer(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("test", "test@example.com", "pass")
        cls.trigger = Trigger.objects.create_for_user(
            cls.user,
            "Test Trigger for User",
            time(9, 0, tzinfo=pytz.utc),
            'RRULE:FREQ=WEEKLY;BYDAY=MO'
        )

    def test_create(self):
        # create a serializer, and ensure .save() gives us a *new* Trigger
        data = {
            'user_id': self.user.id,
            'time': '14:30',
            'name': "Friday reminder",
            'rrule': 'RRULE:FREQ=WEEKLY;BYDAY=FR',
        }
        serializer = CustomTriggerSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # verify validated data
        self.assertEqual(serializer.validated_data['user_id'], self.user.id)
        self.assertEqual(serializer.validated_data['time'], time(14, 30))
        self.assertEqual(serializer.validated_data['name'], 'Friday reminder')
        self.assertEqual(serializer.validated_data['rrule'], 'RRULE:FREQ=WEEKLY;BYDAY=FR')

        # ensure it created the trigger appropriately
        trigger = serializer.save()
        self.assertIsInstance(trigger, Trigger)
        self.assertEqual(trigger.user, self.user)
        self.assertEqual(trigger.time, time(14, 30, tzinfo=pytz.utc))
        self.assertEqual(trigger.name, "Friday reminder")
        self.assertEqual(trigger.recurrences_as_text(), "weekly, each Friday")

    def test_update(self):
        # create a serializer, passing in an existing instance, and ensure
        # .save() gives us an *updated* Trigger

        self.assertEqual(self.trigger.name, "Test Trigger for User")
        self.assertEqual(self.trigger.time,  time(9, 0, tzinfo=pytz.utc))

        # NOTE: all fields are required.
        data = {
            'user_id': self.user.id,
            'name': self.trigger.name,
            'time': '15:00',  # Changed
            'rrule': 'RRULE:FREQ=WEEKLY;BYDAY=TU',  # Changed
        }
        serializer = CustomTriggerSerializer(self.trigger, data=data)
        self.assertTrue(serializer.is_valid())

        # verify validated data
        self.assertEqual(serializer.validated_data['time'], time(15, 0))
        self.assertEqual(serializer.validated_data['rrule'], 'RRULE:FREQ=WEEKLY;BYDAY=TU')

        # ensure it updated the trigger
        trigger = serializer.save()
        self.assertIsInstance(trigger, Trigger)
        self.assertEqual(trigger.user, self.user)
        self.assertEqual(trigger.time, time(15, 0, tzinfo=pytz.utc))
        self.assertEqual(self.trigger.name, "Test Trigger for User")
        self.assertEqual(trigger.recurrences_as_text(), "weekly, each Tuesday")
