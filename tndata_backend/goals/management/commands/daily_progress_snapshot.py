from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from goals.models import DailyProgress, UserCompletedAction
from utils.user_utils import local_day_range

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
            start, end = local_day_range(user)
            self._create_snapshot(user, start, end)
            count += 1
        msg = 'Saved DailyProgress snapshots for {} users'.format(count)
        logger.info(msg)
        self.stdout.write(msg)

    def _create_snapshot(self, user, start, end):
        # Get Today's progress object.
        progress, created = DailyProgress.objects.get_or_create(
            user=user,
            created_on__range=(start, end)
        )

        # Count the number of Behaviors/UserActions selected.
        progress.behaviors_total = user.userbehavior_set.count()
        progress.actions_total = user.useraction_set.count()

        # Count status of UserCompletedAction data for today
        ucas = user.usercompletedaction_set.filter(
            created_on__range=(start, end)
        )
        progress.actions_completed = ucas.filter(
            state=UserCompletedAction.COMPLETED).count()
        progress.actions_snoozed = ucas.filter(
            state=UserCompletedAction.SNOOZED).count()
        progress.actions_dismissed = ucas.filter(
            state=UserCompletedAction.DISMISSED).count()

        # Check on number of CustomAction objects we have today.
        progress.customactions_total = user.customaction_set.count()

        # Count status of UserCompletedAction data for today
        uccas = user.usercompletedcustomaction_set.filter(
            created_on__range=(start, end)
        )
        progress.customactions_completed = uccas.filter(
            state=UserCompletedAction.COMPLETED).count()
        progress.customactions_snoozed = uccas.filter(
            state=UserCompletedAction.SNOOZED).count()
        progress.customactions_dismissed = uccas.filter(
            state=UserCompletedAction.DISMISSED).count()
