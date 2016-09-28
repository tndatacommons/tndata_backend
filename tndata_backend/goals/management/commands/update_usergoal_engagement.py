import waffle
from django.core.management.base import BaseCommand
from goals.models import UserGoal
import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates Goal-specific user engagement data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help=("Restrict this command to the given User. "
                  "Accepts ONLY a user ID")
        )

    def _get_usergoals(self, options):
        if options.get('user'):
            return UserGoal.objects.latest_items(user=options['user'])
        else:
            return UserGoal.objects.latest_items()

    def handle(self, *args, **options):
        # Check to see if we've disabled this, prior to expiring anything.
        if not waffle.switch_is_active('goals-daily-progress-snapshot'):
            return None

        try:
            # WANT: the latest set of userGoal objects per user.
            count = 0
            for ug in self._get_usergoals(options):
                # Update the rank...
                rank = UserGoal.objects.engagement_rank(ug.user, ug.goal)
                ug.engagement_rank = rank

                # And the engagement fields
                ug.calculate_engagement(days=15)
                ug.calculate_engagement(days=30)
                ug.calculate_engagement(days=60)

                ug.save()
                count += 1
        except Exception:
            logger.exception("Failure in update_usergoal_engagement")

        msg = 'Updated {} UserGoal engagement values'.format(count)
        logger.info(msg)
        self.stdout.write(msg)
