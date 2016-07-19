from datetime import datetime
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .. import queue
from .. models import GCMDevice, GCMMessage

User = get_user_model()


def datetime_utc(*args):
    """Make a UTC dateime object."""
    return timezone.make_aware(datetime(*args), timezone.utc)


class TestGCMMessageManager(TestCase):
    """Tests for the `GCMMessageManager`."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        queue.clear()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        cls.user.userprofile.needs_onboarding = False
        cls.user.userprofile.save()

        cls.device = GCMDevice.objects.create(
            user=cls.user,
            registration_id="REGISTRATIONID"
        )
        cls.now = datetime_utc(1999, 2, 1, 13, 30)

        # HACK: We need some object to use as a related, generic FK for the
        # message. Instead of trying to mock this or pulling in an object
        # from another app, just use a GCMDevice, here.
        cls.related_obj = GCMDevice.objects.create(
            user=User.objects.create_user("asdf", "asdf@x.com", "asdf"),
            registration_id="FAKE"
        )

        cls.expired_message = GCMMessage(
            user=cls.user,
            content_object=cls.device,  # HAck
            title="Expired Message",
            message="This is expired",
            success=True,
            deliver_on=datetime_utc(1900, 1, 1, 12, 34),
            expire_on=datetime_utc(1900, 1, 2, 12, 34)
        )
        cls.expired_message.save()

        cls.ready_message = GCMMessage(
            user=cls.user,
            content_object=cls.related_obj,
            title="Ready Message",
            message="This is ready for delivery",
            deliver_on=datetime_utc(1999, 2, 1, 13, 0),
        )
        cls.ready_message.save()

    def test_for_model(self):
        qs = GCMMessage.objects.for_model('gcmdevice')
        self.assertEqual(qs.count(), 2)  # expired & ready messages.

        # Now with a message that has no related objects.
        dt = datetime_utc(2020, 12, 25, 13, 30)
        GCMMessage.objects.create(self.user, "T", "M", dt)
        qs = GCMMessage.objects.for_model('gcmdevice', include_null=True)
        self.assertEqual(qs.count(), 3)

    def test_expired(self):
        # expired == send messages with a set `expire_on` or unsuccessfull
        # messages from the past (3 days ago)
        qs = GCMMessage.objects.expired()
        self.assertEqual(qs.count(), 2)

    def test_ready_for_delivery(self):
        qs = GCMMessage.objects.ready_for_delivery()
        self.assertEqual(qs[0], self.ready_message)

    def test_create(self):
        """Ensure that we can create a Message"""
        other_device = GCMDevice.objects.create(
            user=self.user, registration_id="TESTCREATE"
        )
        msg = GCMMessage.objects.create(
            self.user,
            "New",
            "New Message",
            datetime_utc(2000, 1, 1, 1, 0),
            obj=other_device,  # HACK: we need some object.
        )
        self.assertIsNotNone(msg)
        self.assertEqual(GCMMessage.objects.filter(title="New").count(), 1)

        # Default priority is LOW
        self.assertEqual(msg.priority, GCMMessage.LOW)

        # Clean up
        msg.delete()
        other_device.delete()

    def test_create_with_priority(self):
        """Ensure a priority gets set appropriately."""
        msg = GCMMessage.objects.create(
            self.user,
            "Hello",
            "World",
            datetime_utc(2000, 1, 1, 1, 0),
            priority="high"
        )
        self.assertIsNotNone(msg)
        self.assertEqual(msg.priority, GCMMessage.HIGH)

        # Clean up
        msg.delete()

    def test_create_fails_without_device(self):
        """Ensure a user without a registered device cannot create a message"""
        u = User.objects.create_user('other', 'other@example.com', 'pass')
        with self.assertRaises(GCMDevice.DoesNotExist):
            data = (u, "T", "M", datetime_utc(2000, 1, 1, 1, 0), Mock())
            GCMMessage.objects.create(*data)

        # Clean up.
        u.delete()

    def test_create_fails(self):
        """Ensure that an attempt to create a duplicate returns None"""
        # GCMMessage objects are unique on these fields, together:
        # - user
        # - title
        # - message
        # - deliver_on
        # - object_id
        # - content_type
        msg = GCMMessage.objects.create(
            self.user,
            self.ready_message.title,
            self.ready_message.message,
            self.ready_message.deliver_on,
            self.ready_message.content_object,
        )
        self.assertIsNone(msg)
