import logging

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from userprofile import email
from userprofile.models import UserProfile

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Disables accounts for users that are too young'

    def handle(self, *args, **options):
        # Find all profiles created within the past 2 days...
        dt = timezone.now() - timedelta(days=2)

        disabled_emails = []
        for up in UserProfile.objects.filter(created_on__gte=dt):
            if up.age and up.age < 14:
                # Add them to a list of users to notify & deactivate their
                # account.
                disabled_emails.append(up.user.email)
                up.user.is_active = False
                up.user.save()
                up.save()

                # Also, remove their GCM Device and messages, so they no longer
                # receive any notifications.
                up.user.gcmdevice_set.all().delete()
                for msg in up.user.gcmmessage_set.all():
                    msg.delete()  # removes queued notifications, too

        msg = "Disabled {0} accounts".format(len(disabled_emails))
        logger.error(msg)
        self.stderr.write(msg)

        # Now email them.
        email.send_account_disabled_notification(disabled_emails)
