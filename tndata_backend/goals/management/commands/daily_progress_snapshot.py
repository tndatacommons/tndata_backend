import waffle
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from goals.models import DailyProgress

import logging
logger = logging.getLogger(__name__)


# NOTE: This is a computationall intensive command. So we limit to users
# whose info hasn't been updated in a while (so we don't re-calculate too quickly)
UPDATE_HOURS = 6


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

    def _get_users(self, options):
        User = get_user_model()

        # If a user was specified on the command-line...
        if options['user']:
            try:
                # See if it was a user ID or an email/username.
                if options['user'].isnumeric():
                    criteria = Q(id=options['user'])
                else:
                    criteria = (
                        Q(username=options['user']) | Q(email=options['user'])
                    )
                users = list(User.objects.filter(criteria).distinct())
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(options['user'])
                raise CommandError(msg)

        elif settings.STAGING or settings.DEBUG:
            # Limit to @tndata.org email addresses for staging/debug
            users = User.objects.filter(email__icontains='@tndata.org')
        else:
            # Limit to active users by default
            users = User.objects.filter(is_active=True)

        return users

    def handle(self, *args, **options):
        # Check to see if we've disabled this, prior to expiring anything.
        if not waffle.switch_is_active('goals-daily-progress-snapshot'):
            return None

        # The the relevant set of users
        users = self._get_users(options)

        # Only do this for users whose progress hasn't been updated recently.
        dt = timezone.now() - timedelta(hours=UPDATE_HOURS)
        users = users.exclude(dailyprogress__updated_on__gte=dt).distinct()

        # Create snapshots for those users in the given date range.
        count = 0
        try:
            for user in users:
                progress = DailyProgress.objects.for_today(user)
                progress.update_stats()
                progress.update_behavior_buckets()  # TODO: Remove

                # TODO: Add methods to calculate engagement
                progress.calculate_engagement(days=15)
                progress.calculate_engagement(days=30)
                progress.calculate_engagement(days=60)

                progress.save()
                count += 1
        except Exception as e:
            logger.exception("Failure in daily_progress_snapshot")

        msg = 'Saved DailyProgress snapshots for {} users'.format(count)
        logger.info(msg)
        self.stdout.write(msg)
