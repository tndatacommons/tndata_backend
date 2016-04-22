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

        parser.add_argument(
            '--domain',
            action='store',
            dest='domain',
            default=None,
            help=("Add all users whose email matches a domain, "
                  "e.g. @example.com")
        )

    def _get_users(self, options):
        User = get_user_model()
        users = User.objects.all()

        user = options.get('user')
        domain = options.get('domain')

        if domain:
            if not domain.startswith('@'):
                domain = '@{}'.format(domain)
            users = users.filter(email__iendswith=domain)

        elif user and user.isnumeric():
            users = users.filter(id=user)

        elif user:
            users = users.filter(Q(username=user) | Q(email=user))

        # If we're in staging or dev, only do this for our accounts.
        if settings.STAGING or settings.DEBUG:
            users = users.filter(email__iendswith="@tndata.org")

        if not users.exists():
            raise CommandError("Could not find specified users")

        return users

    def handle(self, *args, **options):
        import ipdb;ipdb.set_trace();
        users = self._get_users(options)

        categories = Category.objects.selected_by_default(state='published')
        for user in users:
            for category in categories:
                category.enroll(user)

        self.stdout.write("Enrolled {} users in {} default categories".format(
            len(users), len(categories)))
