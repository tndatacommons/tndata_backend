import waffle
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

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
        # Check to see if we've disabled this, prior to expiring anything.
        if not waffle.switch_is_active('goals-daily-progress-snapshot'):
            return None

        User = get_user_model()
        if options['user']:
            try:
                if options['user'].isnumeric():
                    criteria = Q(id=options['user'])
                else:
                    criteria = (
                        Q(username=options['user']) | Q(email=options['user'])
                    )
                users = list(User.objects.filter(criteria))
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(options['user'])
                raise CommandError(msg)

        elif settings.STAGING or settings.DEBUG:
            users = User.objects.filter(email__icontains='@tndata.org')

        else:
            users = User.objects.filter(is_active=True)

        # Only do this for users whose progress hasn't been updated recently.
        dt = timezone.today() - timedelta(hours=8)
        users = users.exclude(dailyprogress__updated_on__gte=dt).distinct()

        # Create snapshots for those users in the given date range.
        count = 0
        for user in users:
            progress = DailyProgress.objects.for_today(user)
            progress.update_stats()
            progress.update_behavior_buckets()
            progress.save()
            count += 1
        msg = 'Saved DailyProgress snapshots for {} users'.format(count)
        logger.info(msg)
        self.stdout.write(msg)
