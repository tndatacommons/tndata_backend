from unittest.mock import patch

from datetime import time
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from waffle.testutils import override_switch
from .. models import Action, Trigger, UserAction


class TestCreateNotifications(TestCase):
    """Tests for the `create_notifications` management command."""

    @override_switch('goals-create_notifications', active=True)
    def test_create_notifications_no_content(self):
        log_path = "goals.management.commands.create_notifications.logger"
        with patch(log_path) as logger:
            call_command('create_notifications')

            # We should have logged a 'finished' message
            logger.warning.assert_called_with("Created 0 notifications.")

    @override_switch('goals-create_notifications', active=True)
    def test_create_notifications_with_content(self):
        User = get_user_model()
        user = User.objects.create_user('x', 'x@example.com', 'pass')
        user.userprofile.needs_onboarding = False
        user.userprofile.save()

        # Ensure the user has a device
        user.gcmdevice_set.create(registration_id="REGID", device_name="test")

        # Some test content
        default_trigger = Trigger.objects.create(
            name="default",
            time=time(12, 34),
            recurrences="RRULE:FREQ=DAILY"
        )
        action1 = Action.objects.create(
            title="A1",
            state="published",
            default_trigger=default_trigger,
            notification_text="do A1"
        )
        action2 = Action.objects.create(
            title="A2",
            state="published",
            notification_text="do A2"
        )

        custom_trigger = Trigger.objects.create(
            user=user,
            name="test custom trigger",
            time=time(9, 30),
            recurrences="RRULE:FREQ=DAILY"
        )
        UserAction.objects.create(user=user, action=action1)
        UserAction.objects.create(
            user=user,
            action=action2,
            custom_trigger=custom_trigger
        )

        log_path = "goals.management.commands.create_notifications.logger"
        with patch(log_path) as logger:
            call_command('create_notifications')

            # We should have logged a 'finished' message
            logger.warning.assert_called_with("Created 2 notifications.")

        # Count the number of notifications that should exist for the user.
        self.assertEqual(user.gcmmessage_set.all().count(), 2)
        self.assertEqual(user.gcmmessage_set.filter(content_type=None).count(), 0)
