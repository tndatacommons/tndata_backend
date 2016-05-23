from datetime import datetime, timedelta
from json import dumps
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from pushjack import GCMClient
from pushjack.exceptions import GCMInvalidRegistrationError
from .. models import GCMDevice, GCMMessage
from .. import queue

User = get_user_model()


def datetime_utc(*args):
    """Make a UTC dateime object."""
    return timezone.make_aware(datetime(*args), timezone.utc)


class TestGCMDevice(TestCase):
    """Tests for the `GCMDevice` model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        cls.device = GCMDevice.objects.create(
            user=cls.user,
            registration_id="REGISTRATIONID",
            device_id="DEVICEID"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        queue.clear()

    def test__str__(self):
        # With default values
        expected = "Default Device"
        actual = "{}".format(self.device)
        self.assertEqual(expected, actual)

        # When there's no device name
        expected = "REGISTRATIONID"
        _dn = self.device.device_name
        self.device.device_name = ""
        self.device.save()
        actual = "{}".format(self.device)
        self.assertEqual(expected, actual)
        self.device.device_name = _dn
        self.device.save()

    def test_defaults(self):
        """Ensure fields get default values."""
        self.assertEqual(self.device.device_name, "Default Device")

    def test_constraints(self):
        """Ensure that (user, device_id, registration_id) define a unique
        constraint."""
        with self.assertRaises(IntegrityError):
            GCMDevice.objects.create(
                user=self.user,
                device_id="DEVICEID",
                registration_id='REGISTRATIONID'
            )


class TestGCMMessage(TestCase):
    """Tests for the `GCMMessage` model."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        queue.clear()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        try:
            cls.user.userprofile.timezone = 'America/Chicago'
            cls.user.userprofile.maximum_daily_notifications = 10
            cls.user.userprofile.save()
        except ValueError:
            pass

        cls.device = GCMDevice.objects.create(
            user=cls.user,
            registration_id="REGISTRATIONID"
        )
        cls.msg = GCMMessage.objects.create(
            cls.user,
            "Test",
            "A test message",
            datetime_utc(2000, 1, 1, 1, 0),
            cls.device  # HACK so we have a related object
        )

    def test__str__(self):
        self.assertEqual(
            self.msg.__str__(),
            "{0} on {1}".format(self.msg.title, self.msg.deliver_on)
        )

    def test_get_daily_message_limit(self):
        """Ensure this method fetchs the UserProfile value."""
        self.assertEqual(self.msg.get_daily_message_limit(), 10)

    def test_snooze_hours(self):
        """Ensure deliver_on gets updated correctly when we snooze for an hour"""
        with patch("notifications.models.timezone") as mock_tz:
            now = datetime_utc(1234, 1, 2, 11, 30)
            mock_tz.now.return_value = now

            # When snoozing for an hour, and input is an int
            self.msg.snooze(hours=1)
            expected = datetime_utc(1234, 1, 2, 12, 30)
            self.assertEqual(self.msg.deliver_on, expected)

            # When snoozing for an hour, and input is a list
            self.msg.snooze(hours=[1])
            expected = datetime_utc(1234, 1, 2, 12, 30)
            self.assertEqual(self.msg.deliver_on, expected)

            # When snoozing for an hour, and input is a string
            self.msg.snooze(hours='1')
            expected = datetime_utc(1234, 1, 2, 12, 30)
            self.assertEqual(self.msg.deliver_on, expected)

    def test_snooze_date(self):
        """Ensure deliver_on gets updated correctly when we snooze with a
        specific date."""
        self.msg.snooze(new_datetime=datetime(2015, 9, 1, 15, 30))
        if hasattr(self.user, "userprofile"):
            # User should have a timzone (set to America/Chicago)
            expected = datetime_utc(2015, 9, 1, 20, 30)
        else:
            expected = datetime_utc(2015, 9, 1, 15, 30)
        self.assertEqual(self.msg.deliver_on, expected)

    def test__localize(self):
        _deliver_on = self.msg.deliver_on
        _expire_on = self.msg.expire_on

        self.msg.deliver_on = datetime.now()
        self.msg.expire_on = datetime.now()
        self.assertFalse(timezone.is_aware(self.msg.deliver_on))
        self.assertFalse(timezone.is_aware(self.msg.expire_on))
        self.msg._localize()
        self.assertTrue(timezone.is_aware(self.msg.deliver_on))
        self.assertTrue(timezone.is_aware(self.msg.expire_on))

        # Reset data
        self.msg.deliver_on = _deliver_on
        self.msg.expire_on = _expire_on
        self.msg.save()

    def test_save(self):
        """Save should call _localize."""
        mock_localize = Mock(return_value=datetime_utc(2000, 1, 2, 3, 30))

        # HACK: need a new object to associate a mesage with.
        obj = GCMDevice.objects.create(user=self.user, registration_id="NEW")

        GCMMessage._localize = mock_localize
        msg = GCMMessage.objects.create(
            self.user,
            "ASDF",
            "A asdf message",
            datetime_utc(2000, 1, 1, 1, 0),
            obj,
        )
        mock_localize.assert_any_call()

        # clean up.
        obj.delete()
        msg.delete()

    def test_sending_doesnt_reenque_on_success(self):
        """INTEGRATION: Send to GCM, get a response, and save the object ...
        this should not re-enque the message if it was successful.

        """
        msg = GCMMessage.objects.create(
            self.user,
            "Test",
            "A test message",
            timezone.now(),
            self.device  # HACK so we have a related object
        )
        self.assertNotEqual(msg.queue_id, '')  # should ahve a queue id

        # Set up a mock response from GCM
        mock_resp = Mock(
            responses=[Mock(status_code=200, reason='OK', url="FOO")],
            messages=[{'registration_ids': ['REGISTRATION_ID']}],
            errors=[],
            data=[{
                'canonical_ids': 0,
                'failure': 0,
                'multicast_id': 7793705921315893230,
                'results': [{'message_id': '0:1458839695947903%96e94613f9fd7ecd'}],
                'success': 1,
            }]
        )

        # Set up a mock client so we dont' actually Send to GCM
        mock_client = Mock()
        mock_client.send.return_value = mock_resp
        msg._get_gcm_client = Mock(return_value=mock_client)

        # 1. call send() / whose internals are mocked
        # 2. it'll call _handle_gcm_response
        # 3. which will call save()
        # 4. which should not re-enque the message.
        original_queue_id = msg.queue_id
        msg.send()

        self.assertEqual(msg.queue_id, original_queue_id)
        self.assertTrue(msg.success)
        self.assertEqual(msg.response_code, 200)
        self.assertEqual(msg.registration_ids, "REGISTRATION_ID")
        self.assertEqual(msg.response_data['android'], mock_resp.data)

        # Clean up.
        msg.delete()

    def test__get_gcm_client(self):
        client = self.msg._get_gcm_client()
        self.assertIsInstance(client, GCMClient)
        self.assertEqual(client.api_key, settings.GCM['API_KEY'])

    def test_android_devices(self):
        self.assertEqual(self.msg.android_devices, ['REGISTRATIONID'])

    def test_ios_devices(self):
        # note: the message above is only associated with an android device.
        self.assertEqual(self.msg.ios_devices, [])

        # Create a new Device / message for ios
        device = GCMDevice.objects.create(
            user=self.user,
            device_name='IOS',
            device_id='test ios device',
            registration_id="IOS",
            device_type='ios'
        )
        msg = GCMMessage.objects.create(
            self.user,
            "Test ios message",
            "A test message for an ios device",
            datetime_utc(2000, 1, 1, 1, 0),
            device
        )
        self.assertEqual(msg.ios_devices, ['IOS'])

        # clean up
        msg.delete()
        device.delete()

    def test__checkin(self):
        from goals.settings import (
            DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE,
            DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE
        )
        # Input does not change when it's an action
        obj = {'object_id': 123, 'object_type': 'action', 'title': ''}
        result = self.msg._checkin(obj)
        self.assertDictEqual(obj, result)

        # Input does not change when it's null
        obj = {'object_id': None, 'object_type': None, 'title': ''}
        result = self.msg._checkin(obj)
        self.assertDictEqual(obj, result)

        # Input does change when it's a goal with no object ID
        obj = {
            'object_id': None,
            'object_type': 'goal',
            'title': DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE
        }
        result = self.msg._checkin(obj)
        expected = {
            'object_id': 1,
            'object_type': 'checkin',
            'title': DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE
        }
        self.assertDictEqual(result, expected)

        # Input does change when it's a goal with no object ID
        obj = {
            'object_id': None,
            'object_type': 'goal',
            'title': DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE
        }
        result = self.msg._checkin(obj)
        expected = {
            'object_id': 2,
            'object_type': 'checkin',
            'title': DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE,
        }
        self.assertDictEqual(result, expected)

    def test_content(self):
        self.assertEqual(
            self.msg.content,
            {
                "id": self.msg.id,
                "title": "Test",
                "message": "A test message",
                "object_type": "gcm device",
                "object_id": self.device.id,
                "user_mapping_id": None,
                "production": not (settings.DEBUG or settings.STAGING),
            }
        )

    def test_content_when_content_object_mapping_is_an_int(self):
        """If the content_object.get_user_mapping returns an integer"""
        # Add a mock 'get_user_mapping' to our content_object for this test...
        self.msg.content_object.get_user_mapping = Mock(return_value=-1)
        self.assertEqual(
            self.msg.content,
            {
                "id": self.msg.id,
                "title": "Test",
                "message": "A test message",
                "object_type": 'gcm device',
                "object_id": self.device.id,
                "user_mapping_id": -1,  # Mocked value
                "production": not (settings.DEBUG or settings.STAGING),
            }
        )
        # Remove the mocked method.
        del self.msg.content_object.get_user_mapping

    def test_content_with_no_content_object(self):
        msg = GCMMessage.objects.create(
            self.user,
            "ASDF",
            "A asdf message",
            datetime_utc(2000, 1, 1, 1, 0),
        )
        self.assertEqual(
            msg.content,
            {
                "id": msg.id,
                "title": "ASDF",
                "message": "A asdf message",
                "object_type": None,
                "object_id": None,
                "user_mapping_id": None,
                "production": not (settings.DEBUG or settings.STAGING),
            }
        )

    def test_content_json(self):
        self.assertEqual(self.msg.content_json, dumps(self.msg.content))

    def test_content_json_with_no_content_object(self):
        msg = GCMMessage.objects.create(
            self.user,
            "ASDF",
            "A asdf message",
            datetime_utc(2000, 1, 1, 1, 0),
        )
        expected = dumps({
            "id": msg.id,
            "title": "ASDF",
            "message": "A asdf message",
            "object_type": None,
            "object_id": None,
            "user_mapping_id": None,
            "production": not (settings.DEBUG or settings.STAGING),
        })
        self.assertEqual(msg.content_json, expected)

    def test_send(self):
        with patch("notifications.models.GCMClient") as mock_client:
            # Don't actually call these internal record-keeping methods.
            self.msg._handle_gcm_response = Mock()
            self.msg._remove_invalid_gcm_devices = Mock()
            self.msg._set_expiration = Mock()

            # mock the call / response from GCM
            mock_resp = Mock(
                status_code=200,
                reason='ok',
                url='url',
                errors=[],
            )
            mock_client.return_value = Mock(**{'send.return_value': mock_resp})

            self.assertTrue(self.msg.send())
            mock_client.return_value.send.assert_called_once_with(
                ['REGISTRATIONID'],
                self.msg.content_json,
                delay_while_idle=False,
                low_priority=True,
                time_to_live=None,
            )

    def test__set_expiration(self):
        other_device = GCMDevice.objects.create(
            user=self.user, registration_id="OTHER")
        msg = GCMMessage.objects.create(
            self.user,
            "Other",
            "Another message",
            datetime_utc(2000, 1, 1, 1, 0),
            other_device,  # HACK: we need some object.
        )

        # When the message has not be marked a "success" (the default)
        self.assertIsNone(msg.expire_on)
        msg._set_expiration()
        self.assertIsNone(msg.expire_on)  # Should be unchanged

        # When it *is* successful
        msg.success = True
        msg.save()
        with patch("notifications.models.timezone") as mock_tz:
            date = datetime_utc(2015, 5, 16, 15, 30)
            mock_tz.now.return_value = date
            msg._set_expiration()
            self.assertEqual(msg.expire_on, date + timedelta(days=7))

        # Clean up
        msg.delete()
        other_device.delete()

    def test__handle_gcm_response(self):
        """Ensure that success=True, and the response_text includes expected
        data (from the GCM response)"""
        resp = Mock(status_code=200, reason='OK', url="FOO")
        # This mock response includes an example of GCM data that we'd get
        # when a message is delivered successfully.
        mock_resp = Mock(
            responses=[resp],
            messages=[{'registration_ids': ['REGISTRATION_ID']}],
            errors=[],
            data=[{
                'canonical_ids': 0,
                'failure': 0,
                'multicast_id': 5629976388209913698,
                'results': [{'message_id': '0:1458839695947903%96e94613f9fd7ecd'}],
                'success': 1
            }]
        )
        self.msg._handle_gcm_response(mock_resp)
        expected_text = "Status Code: 200\nReason: OK\nURL: FOO\n----\n"

        self.assertTrue(self.msg.success)
        self.assertEqual(self.msg.response_text, expected_text)
        self.assertEqual(self.msg.response_code, 200)
        self.assertEqual(self.msg.registration_ids, "REGISTRATION_ID")
        self.assertEqual(self.msg.response_data['android'], mock_resp.data)

    def test__handle_gcm_response_when_error(self):
        """Ensure that success=False, and our response_text includes the GCM
        error message."""
        resp = Mock(status_code=200, reason='OK', url="FOO")
        mock_resp = Mock(
            responses=[resp],
            messages=[{'registration_ids': ['REGISTRATION_ID']}],
            errors=[],
            data=[{
                'canonical_ids': 0,
                'failure': 1,
                'multicast_id': 8056733761717334109,
                'results': [{'error': 'NotRegistered'}],
                'success': 0
            }]
        )
        self.msg._handle_gcm_response(mock_resp)

        self.assertIn("NotRegistered", self.msg.response_text)
        self.assertEqual(self.msg.response_code, 200)
        self.assertEqual(self.msg.registration_ids, "REGISTRATION_ID")
        self.assertEqual(self.msg.response_data['android'], mock_resp.data)

    def test__handle_gcm_response_when_success_and_error(self):
        """If we get both a success and a failure in the GCM result data,
        record the message as a success."""
        resp = Mock(status_code=200, reason='OK', url="FOO")
        mock_resp = Mock(
            responses=[resp],
            messages=[{'registration_ids': ['REGISTRATION_ID']}],
            errors=[],
            data=[{
                'canonical_ids': 0,
                'failure': 1,
                'multicast_id': 8176922708522956541,
                'results': [{'message_id': '0:1458842868372097%96e94613f9fd7ecd'},
                            {'error': 'NotRegistered'}],
                'success': 1
            }]
        )
        self.msg._handle_gcm_response(mock_resp)

        success_text = "Status Code: 200\nReason: OK\nURL: FOO\n----\n"
        error_text = "NotRegistered"
        self.assertIn(success_text, self.msg.response_text)
        self.assertIn(error_text, self.msg.response_text)
        self.assertEqual(self.msg.response_code, 200)
        self.assertEqual(self.msg.registration_ids, "REGISTRATION_ID")
        self.assertEqual(self.msg.response_data['android'], mock_resp.data)

    def test__handle_gcm_response_when_multiple_successes(self):
        """If we get multiple successes in the GCM result data, record the
        message as a success."""

        resp = Mock(status_code=200, reason='OK', url="FOO")
        # This mock response includes an example of GCM data that we'd get
        # when a message is delivered successfully.
        mock_resp = Mock(
            responses=[resp],
            messages=[{'registration_ids': ['REGISTRATION_ID']}],
            errors=[],
            data=[{
                'canonical_ids': 0,
                'failure': 0,
                'multicast_id': 7793705921315893230,
                'results': [
                    {'message_id': '0:1458839695947903%96e94613f9fd7ecd'},
                    {'message_id': '0:2458839695947903%96e94613f9fd7ecd'}
                ],
                'success': 2
            }]
        )

        self.msg._handle_gcm_response(mock_resp)
        expected_text = (
            "Status Code: 200\nReason: OK\nURL: FOO\n----\n"
            "Status Code: 200\nReason: OK\nURL: FOO\n----\n"
        )
        self.assertTrue(self.msg.success)
        self.assertIn(expected_text, self.msg.response_text)
        self.assertEqual(self.msg.response_code, 200)
        self.assertEqual(self.msg.registration_ids, "REGISTRATION_ID")
        self.assertEqual(self.msg.response_data['android'], mock_resp.data)

    def test__handle_gcm_response_error_invalid_identifier(self):
        """Handle the case where we get an error message from GCM about an
        invalid registration id / identifier. The matching GCMDevice should
        be removed.

        """
        # Create a new device / message.
        GCMDevice.objects.create(user=self.user, registration_id="XXX")
        message = GCMMessage.objects.create(
            self.user,
            "Another Test",
            "Another test message",
            datetime_utc(2000, 1, 1, 1, 0),
        )

        # The HTTP response from GCM
        resp = Mock(
            status_code=200,
            reason='OK',
            url="https://android.googleapis.com/gcm/send"
        )

        # This mock pushjack response includes an example of GCM data that we'd
        # get when a message was not delivered due to an invalid registration id
        error = GCMInvalidRegistrationError('XXX')

        mock_resp = Mock(
            responses=[resp],
            errors=[error],
            failures=['XXX'],
            registration_ids=['XXX'],
            messages=[{'to': 'XXX', }],
            data=[{
                'success': 0,
                'canonical_ids': 0,
                'failure': 1,
                'multicast_id': 5313178907646522818,
                'results': [{'error': 'InvalidRegistration'}]
            }]
        )

        # Verify we have a GCM Device.
        self.assertTrue(GCMDevice.objects.filter(registration_id='XXX').exists())

        # Handle the response
        message._handle_gcm_response(mock_resp)

        # Verify the side effect: The message should be marked as unsuccessful
        self.assertFalse(message.success)
