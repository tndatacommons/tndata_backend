import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from goals.models import CustomAction, UserAction
from utils.slack import post_private_message

logger = logging.getLogger("loggly_logs")


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

    def _user_kwargs(self, user):
        User = get_user_model()

        kwargs = {}  # Keyword arguments that get passed to our action querysets.
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
        return kwargs

    def handle(self, *args, **options):
        count = 0
        kwargs = self._user_kwargs(options['user'])

        # Fetch the set of UserActions to refresh.
        useractions = UserAction.objects.stale(**kwargs).published()

        # If we're in staging or dev, only do this for our accounts.
        if settings.STAGING or settings.DEBUG:
            useractions = useractions.filter(user__email__icontains="@tndata.org")

        for ua in useractions:
            count += 1
            ua.save(update_triggers=True)  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} UserActions".format(count)
        logger.error(msg)
        self.stderr.write(msg)
        #post_private_message("bkmontgomery", msg)

        count = 0
        for ca in CustomAction.objects.stale(**kwargs):
            count += 1
            ca.save()  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} CustomActions".format(count)
        logger.error(msg)
        self.stderr.write(msg)
        #post_private_message("bkmontgomery", msg)
