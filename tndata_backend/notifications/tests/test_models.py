import pytz
from datetime import datetime, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .. models import (
    GCMDevice,
    GCMMessage,
)

User = get_user_model()


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
