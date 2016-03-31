from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from waffle.testutils import override_switch

from .. import queue
from .. models import GCMDevice, GCMMessage

User = get_user_model()


def datetime_utc(*args):
    """Make a UTC dateime object."""
    return timezone.make_aware(datetime(*args), timezone.utc)


class TestExpireMessages(TestCase):
    """Tests for the `expire_messages` management command."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        queue.clear()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
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

    @override_switch('notifications-expire', active=True)
    def test_expire_messages(self):
        log_path = "notifications.management.commands.expire_messages.logger"
        with patch(log_path) as logger:
            call_command('expire_messages')

            # We should have logged a 'finished' message
            logger.info.assert_called_with("Expired 1 GCM Messages")
