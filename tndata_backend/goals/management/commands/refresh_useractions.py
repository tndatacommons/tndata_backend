import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from goals.sequence import get_next_useractions_in_sequence
from goals.models import CustomAction, UserAction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates the next_trigger_date field for stale UserActions and CustomActions.'

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
            '--hours',
            action='store',
            dest='hours',
            default=2,
            type=int,
            help="Limit to objects that are older than the given value (in hours)"
        )
        parser.add_argument(
            '--limit',
            action='store',
            dest='limit',
            default=100,
            type=int,
            help="Limit the number of objects that are modified"
        )

    def _users(self, user):
        """Pull the `user` option and return a QuerySet of active Users."""
        User = get_user_model()
        users = User.objects.filter(is_active=True)
        if user and user.isnumeric():
            users = users.filter(id=user)
        elif user:
            users = users.filter(Q(username=user) | Q(email=user))

        # Restrict to internal users for staging and/or debug
        if settings.STAGING or settings.DEBUG:
            users = users.filter(email__icontains="@tndata.org")
        return users

    def _useraction_kwargs(self, user):
        """Pull the `user` option and create a dict of keyword arguments
        that can be passed to the UserAction query.

        """
        User = get_user_model()

        kwargs = {}
        if user:
            try:
                if user.isnumeric():
                    criteria = Q(id=user)
                else:
                    criteria = (Q(username=user) | Q(email=user))
                kwargs['user'] = User.objects.get(criteria)
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(user)
                raise CommandError(msg)

        # Restrict to internal users for staging and/or debug
        if settings.STAGING or settings.DEBUG:
            kwargs['user__email__icontains'] = "@tndata.org"

        return kwargs

    def handle(self, *args, **options):
        # Limit the refreshed objects to those that are at least 2 hours old.
        # (or to an age based on limit option)
        limit = options.pop('limit')
        hours = options.pop('hours')

        # If we passed in a user, dont' limit results
        if options['user'] is not None:
            limit = None

        # 1. Fetch the set of SEQUENCED UserActions to refresh.
        count = 0
        for user in self._users(options['user']):
            useractions = get_next_useractions_in_sequence(user)
            useractions = useractions.stale(hours=hours).published()
            for ua in useractions:
                count += 1
                ua.save(update_triggers=True)  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} UserActions".format(count)
        logger.info(msg)
        self.stdout.write(msg)

        # 2. Refresh stale UserActions that have a custom trigger
        count = 0
        kwargs = self._useraction_kwargs(options['user'])
        kwargs['hours'] = hours
        useractions = UserAction.objects.stale(
            hours=hours,
            custom_trigger__isnull=False
        )
        for ua in useractions.published()[:limit]:
            count += 1
            ua.save(update_triggers=True)

        msg = "Refreshed Custom Triggers for {0} UserActions".format(count)
        logger.info(msg)
        self.stdout.write(msg)

        # 3. Update all custom actions
        count = 0
        for ca in CustomAction.objects.stale(**kwargs):
            count += 1
            ca.save()  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} CustomActions".format(count)
        logger.info(msg)
        self.stdout.write(msg)
