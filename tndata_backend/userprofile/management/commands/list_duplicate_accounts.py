from collections import Counter

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Detects & Removes (disables) duplicate accounts.'

    def write(self, output):
        self.stdout.write("{}\n".format(output))

    def handle(self, *args, **options):
        # Find all accounts with duplicate emails.
        User = get_user_model()
        emails = Counter(User.objects.values_list("email", flat=True))
        emails = [email for email, count in emails.items() if count > 1]

        self.write("\nFound {} duplicate accounts\n".format(len(emails)))
        users = User.objects.filter(email__in=emails)
        users = users.order_by("email", "date_joined")
        prev_email = ''
        for user in users:
            msg = "{}] <{}> {}"
            self.write(msg.format(user.date_joined, user.email, user.get_full_name()))
            if user.email == prev_email:
                msg = " -> {}/admin/auth/user/?q={}\n"
                self.write(msg.format(settings.SITE_URL, user.email))
            prev_email = user.email
