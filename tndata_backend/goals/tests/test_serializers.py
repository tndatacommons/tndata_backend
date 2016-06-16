import pytz
from datetime import date, time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from rest_framework import serializers
from utils.serializer_fields import ReadOnlyDatetimeField

from .. models import Trigger
from .. serializers import CustomTriggerSerializer

User = get_user_model()


DRF_DT_FORMAT = settings.REST_FRAMEWORK['DATETIME_FORMAT']
TEST_REST_FRAMEWORK = {
    'PAGE_SIZE': 100,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'utils.api.BrowsableAPIRendererWithoutForms',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'utils.api.NoThrottle',
    ),
    'VERSION_PARAM': 'version',
    'DEFAULT_VERSION': '1',
    'ALLOWED_VERSIONS': ['1', '2'],
    'DEFAULT_VERSIONING_CLASS': 'utils.api.DefaultQueryParamVersioning',
    'DATETIME_FORMAT': DRF_DT_FORMAT,
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestReadOnlyDatetimeField(TestCase):
    """Tests for our ReadOnlyDatetimeField. These are based on the ReadOnlyField
    from DRF: https://goo.gl/bRSzw6 """

    def setUp(self):
        class TestSerializer(serializers.Serializer):
            dt = ReadOnlyDatetimeField()
        self.serializer_class = TestSerializer

    def test_validate_read_only(self):
        """This is indeed a read-only field"""
        dt = timezone.now()
        serializer = self.serializer_class(data={'dt': dt})
        self.assertTrue(serializer.is_valid())
        assert serializer.validated_data == {}

    def test_serialize_read_only(self):
        """Read-only serializers.should be serialized."""
        dt = timezone.now()
        serializer = self.serializer_class({'dt': dt})
        assert serializer.data == {'dt': dt.strftime(DRF_DT_FORMAT)}


class TestCustomTriggerSerializer(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("test", "test@example.com", "pass")

    def setUp(self):
        self.trigger = Trigger.objects.create_for_user(
            self.user,
            "Test Trigger for User",
            time(9, 0, tzinfo=pytz.utc),
            None,
            'RRULE:FREQ=WEEKLY;BYDAY=MO'
        )

    def tearDown(self):
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_create(self):
        # create a serializer, and ensure .save() gives us a *new* Trigger
        data = {
            'user_id': self.user.id,
            'date': '',
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
        self.assertIsNone(serializer.validated_data.get('date'))

        # ensure it created the trigger appropriately
        trigger = serializer.save()
        self.assertIsInstance(trigger, Trigger)
        self.assertEqual(trigger.user, self.user)
        self.assertEqual(trigger.time, time(14, 30, tzinfo=pytz.utc))
        self.assertEqual(trigger.name, "Friday reminder")
        self.assertEqual(trigger.recurrences_as_text(), "weekly, each Friday")

    def test_create_with_date_and_time_only(self):
        # create a serializer, providing only a date/time, and ensure
        # .save() gives us a *new* Trigger
        data = {
            'user_id': self.user.id,
            'time': '23:59',
            'name': "New Years",
            'date': '2016-01-01'
        }
        serializer = CustomTriggerSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # verify validated data
        self.assertEqual(serializer.validated_data['user_id'], self.user.id)
        self.assertEqual(serializer.validated_data['name'], 'New Years')
        self.assertEqual(serializer.validated_data['time'], time(23, 59))
        self.assertEqual(serializer.validated_data['date'], date(2016, 1, 1))
        self.assertIsNone(serializer.validated_data.get('rrule'))

        # ensure it created the trigger appropriately
        trigger = serializer.save()
        self.assertIsInstance(trigger, Trigger)
        self.assertEqual(trigger.user, self.user)
        self.assertEqual(trigger.time, time(23, 59, tzinfo=pytz.utc))
        self.assertEqual(trigger.name, "New Years")
        self.assertEqual(trigger.trigger_date, date(2016, 1, 1))
        self.assertEqual(trigger.recurrences_as_text(), "")

    def test_update(self):
        # create a serializer, passing in an existing instance, and ensure
        # .save() gives us an *updated* Trigger

        self.assertEqual(self.trigger.name, "Test Trigger for User")
        self.assertEqual(self.trigger.time,  time(9, 0, tzinfo=pytz.utc))

        data = {
            'user_id': self.user.id,
            'date': '',
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

    def test_empty_trigger_data(self):
        """ensure the serializer works with empty trigger data (which sould
        essentially disable the trigger)."""

        data = {
            'user_id': self.user.id,
            'name': self.trigger.name,
            'date': '',
            'time': '',
            'rrule': '',
        }
        serializer = CustomTriggerSerializer(self.trigger, data=data)
        self.assertTrue(serializer.is_valid())

        # verify validated data
        self.assertIsNone(serializer.validated_data['date'])
        self.assertIsNone(serializer.validated_data['time'])
        self.assertIsNone(serializer.validated_data['rrule'])

        # ensure it updated the trigger
        trigger = serializer.save()
        self.assertIsInstance(trigger, Trigger)
        self.assertEqual(self.trigger.name, "Test Trigger for User")
        self.assertEqual(trigger.user, self.user)
        self.assertIsNone(trigger.recurrences)
        self.assertIsNone(trigger.trigger_date)
        self.assertIsNone(trigger.time)

        # ALLOW None values
        data = {
            'user_id': self.user.id,
            'name': self.trigger.name,
            'date': None,
            'time': None,
            'rrule': None,
        }
        serializer = CustomTriggerSerializer(self.trigger, data=data)
        self.assertTrue(serializer.is_valid())

        # verify validated data
        self.assertIsNone(serializer.validated_data['date'])
        self.assertIsNone(serializer.validated_data['time'])
        self.assertIsNone(serializer.validated_data['rrule'])
