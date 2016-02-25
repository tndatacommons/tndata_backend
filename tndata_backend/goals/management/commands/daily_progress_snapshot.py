from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from goals.models import DailyProgress

import logging
logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Creates a daily snapshot for user progress data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help=("Create snapshots for a given User. "
                  "Accepts a username, email, or id")
        )

    def handle(self, *args, **options):
        User = get_user_model()
        if options['user']:
            try:
                if options['user'].isnumeric():
                    criteria = Q(id=options['user'])
                else:
                    criteria = (
                        Q(username=options['user']) | Q(email=options['user'])
                    )
                users = list(User.objects.get(criteria))
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(options['user'])
                raise CommandError(msg)
        else:
            users = User.objects.filter(is_active=True)

        # Create snapshots for those users in the given date range.
        count = 0
        for user in users:
            progress = DailyProgress.objects.for_today(user)
            progress.update_stats()
            count += 1
        msg = 'Saved DailyProgress snapshots for {} users'.format(count)
        logger.info(msg)
        self.stdout.write(msg)
