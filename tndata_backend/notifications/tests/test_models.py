from datetime import datetime, timedelta
from json import dumps
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from pushjack import GCMClient
from .. models import GCMDevice, GCMMessage


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
        self.assertTrue(self.device.is_active)

    def test_constraints(self):
        """Ensure that (user, registration_id) define a unique constraint."""
        with self.assertRaises(IntegrityError):
            GCMDevice.objects.create(
                user=self.user,
                registration_id='REGISTRATIONID'
            )


class TestGCMMessage(TestCase):
    """Tests for the `GCMMessage` model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        try:
            cls.user.userprofile.timezone = 'America/Chicago'
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

    def test__get_gcm_client(self):
        client = self.msg._get_gcm_client()
        self.assertIsInstance(client, GCMClient)
        self.assertEqual(client.api_key, settings.GCM['API_KEY'])

    def test_registered_devices(self):
        self.assertEqual(
            self.msg.registered_devices,
            ['REGISTRATIONID']
        )

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
            }
        )

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
        })
        self.assertEqual(msg.content_json, expected)

    def test_send(self):
        with patch("notifications.models.GCMClient") as mock_client:
            self.msg._save_response = Mock()  # Don't call _save_response
            mock_resp = Mock(
                status_code=200,
                reason='ok',
                url='url',
            )
            mock_client.return_value = Mock(**{'send.return_value': mock_resp})

            self.assertEqual(self.msg.send(), mock_resp)
            mock_client.return_value.send.assert_called_once_with(
                ['REGISTRATIONID'],
                self.msg.content_json,
                delay_while_idle=False,
                time_to_live=None,
            )

    def test__set_expiration(self):
        other_device = GCMDevice.objects.create(user=self.user, registration_id="OTHER")
        msg = GCMMessage.objects.create(
            self.user,
            "Other",
            "Another message",
            datetime_utc(2000, 1, 1, 1, 0),
            other_device,  # HACK: we need some object.
        )

        # When no response code is set:
        self.assertIsNone(msg.expire_on)
        msg._set_expiration()
        self.assertIsNone(msg.expire_on)  # Should be unchanged

        # When there is a resposne code (of 200)
        msg.response_code = 200
        msg.save()
        with patch("notifications.models.timezone") as mock_tz:
            date = datetime_utc(2015, 5, 16, 15, 30)
            mock_tz.now.return_value = date
            msg._set_expiration()
            self.assertEqual(msg.expire_on, date + timedelta(days=7))

        # Clean up
        msg.delete()
        other_device.delete()

    def test__save_response(self):
        resp = Mock(status_code=200, reason='OK', url="FOO")
        mock_resp = Mock(
            responses=[resp],
            messages=[{'registration_ids': ['REGISTRATION_ID']}],
            data=[{'some': 'data'}]
        )
        self.msg._save_response(mock_resp)

        expected_text = "Status Code: 200\nReason: OK\nURL: FOO\n----\n"
        self.assertEqual(self.msg.response_text, expected_text)
        self.assertEqual(self.msg.response_code, 200)
        self.assertEqual(self.msg.registration_ids, "REGISTRATION_ID")
        self.assertEqual(self.msg.response_data, [{'some': 'data'}])
