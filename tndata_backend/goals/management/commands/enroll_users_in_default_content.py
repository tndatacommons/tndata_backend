import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from goals.models import Category

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Enroll a user or users in the set of default Categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help=("Restrict this command to the given User. "
                  "Accepts a username, email, or id")
        )

    def _get_users(self, user):
        User = get_user_model()
        if user:
            try:
                if user.isnumeric():
                    criteria = Q(id=user)
                else:
                    criteria = (Q(username=user) | Q(email=user))

                # If we're in staging or dev, only do this for our accounts.
                if settings.STAGING or settings.DEBUG:
                    criteria = (criteria & Q(email__icontains="@tndata.org"))

                return [User.objects.get(criteria)]
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(user)
                raise CommandError(msg)
        return User.objects.all()

    def handle(self, *args, **options):
        users = self._get_users(options['user'])

        categories = Category.objects.selected_by_default(state='published')
        for user in users:
            for category in categories:
                category.enroll(user)

        self.stdout.write("Enrolled {} users in {} default categories".format(
            len(users), len(categories)))
