from datetime import datetime
from hashlib import md5
from json import dumps
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from pushjack import GCMClient
from .. models import (
    GCMDevice,
    GCMMessage,
)

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
            registration_id="REGISTRATIONID"
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
        with patch("notifications.models.datetime") as mock_dt:
            now = datetime_utc(1234, 1, 2, 11, 30)
            nowstring = now.strftime("%c")
            mock_dt.utcnow.return_value = now
            content_info = "{0}-{1}-{2}-{3}".format(
                nowstring,
                self.msg.content_type.name,
                self.msg.object_id,
                self.user.id
            )
            expected = md5(content_info.encode("utf8")).hexdigest()
            self.msg._set_message_id()  # ensure it's set correctly
            actual = "{}".format(self.msg)
            self.assertEqual(expected, actual)

    def test__set_message_id(self):
        with patch("notifications.models.datetime") as mock_dt:
            now = datetime_utc(1234, 1, 2, 11, 30)
            nowstring = now.strftime("%c")
            mock_dt.utcnow.return_value = now
            content_info = "{0}-{1}-{2}-{3}".format(
                nowstring,
                self.msg.content_type.name,
                self.msg.object_id,
                self.user.id
            )
            expected = md5(content_info.encode("utf8")).hexdigest()
            self.msg._set_message_id()  # Call the method.
            self.assertEqual(self.msg.message_id, expected)  # check result

    def test__set_message_id_when_no_content_object(self):
        """Ensure this still works if there's no content_object."""
        with patch("notifications.models.datetime") as mock_dt:
            date = datetime_utc(2015, 5, 16, 15, 30)
            mock_dt.utcnow.return_value = date

            alert_date = datetime_utc(2014, 5, 30, 14, 45)
            msg = GCMMessage.objects.create(
                self.user, "NEW Test", "another message", alert_date
            )
            expected = md5(date.strftime("%c").encode("utf8")).hexdigest()
            self.assertEqual(msg.message_id, expected)

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
        """Save should call _localize and _set_message_id."""
        mock_localize = Mock(return_value=datetime_utc(2000, 1, 2, 3, 30))
        mock_set_message_id = Mock(return_value="MESSAGEID")

        # HACK: need a new object to associate a mesage with.
        obj = GCMDevice.objects.create(user=self.user, registration_id="NEW")

        GCMMessage._localize = mock_localize
        GCMMessage._set_message_id = mock_set_message_id
        msg = GCMMessage.objects.create(
            self.user,
            "ASDF",
            "A asdf message",
            datetime_utc(2000, 1, 1, 1, 0),
            obj,
        )
        mock_localize.assert_any_call()
        mock_set_message_id.assert_any_call()

        # clean up.
        obj.delete()
        msg.delete()

    def test__get_gcm_client(self):
        client = self.msg._get_gcm_client()
        self.assertIsInstance(client, GCMClient)
        self.assertEqual(client.api_key, settings.GCM['API_KEY'])

    def test_registration_ids(self):
        self.assertEqual(
            self.msg.registration_ids,
            ['REGISTRATIONID']
        )

    def test_content(self):
        self.assertEqual(
            self.msg.content,
            {
                "title": "Test",
                "message": "A test message",
                "object_type": "gcm device",
                "object_id": self.device.id,
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
                "title": "ASDF",
                "message": "A asdf message",
                "object_type": None,
                "object_id": None,
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
            "title": "ASDF",
            "message": "A asdf message",
            "object_type": None,
            "object_id": None,
        })
        self.assertEqual(msg.content_json, expected)

    def test_send(self):
        with patch("notifications.models.GCMClient") as mock_client:
            resp = Mock(responses=[Mock(status_code=200, reason='ok', url='url')])
            mock_client.return_value = Mock(**{'send.return_value': resp})

            self.assertEqual(self.msg.send(), resp)
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
            self.assertEqual(msg.expire_on, date)

        # Clean up
        msg.delete()
        other_device.delete()

    def test__save_response(self):
        mock_resp = Mock(responses=[Mock(**{
            'status_code': 200,
            'reason': 'OK',
            'url': 'FOO',
        })])
        self.msg._save_response(mock_resp)

        expected_text = "Status Code: 200\nReason: OK\nURL: FOO\n----\n"
        self.assertEqual(self.msg.response_text, expected_text)
        self.assertEqual(self.msg.response_code, 200)
