import logging

from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from goals.models import BehaviorProgress, GoalProgress, CategoryProgress


logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Updates BehaviorProgress, and creates GoalProgress/CategoryProgress. Run Nightly'

    def handle(self, *args, **options):
        User = get_user_model()

        err_msg = "Failed to generate scores for {0}"
        bp_count = 0
        gp_count = 0  # for aggregate action info

        gp_scores_count = 0  # for aggreage behavior info
        cp_scores_count = 0

        try:
            # Update BehaviorProgress instances in some time period, so they
            # re-calculate stats for completed actions
            date = timezone.now() - timedelta(days=settings.PROGRESS_HISTORY_DAYS)
            for bp in BehaviorProgress.objects.filter(reported_on__gte=date):
                bp.save()  # Calls BehaviorProgress._calculate_action_progress
                bp_count += 1
        except Exception:
            logger.error(err_msg.format("BehaviorProgress"), exc_info=1)

        try:
            # Generate scores for goal progress for all users that have
            # selected one or more Goals.
            for user in User.objects.filter(usergoal__isnull=False).distinct():
                objs = GoalProgress.objects.generate_scores(user)
                gp_scores_count += objs.count()
            logger.info("Generated scores for GoalProgress")
        except Exception:
            logger.error(err_msg.format("GoalProgress"), exc_info=1)

        try:
            # Re-calculate action progress stats for GoalProgress objects over
            # the history range in which we're interested.
            dt = timezone.now() - timedelta(days=settings.PROGRESS_HISTORY_DAYS)
            for gp in GoalProgress.objects.filter(reported_on__contains=dt.date()):
                gp.save()  # Triggers the re-calculation
                gp_count += 1
        except Exception:
            logger.error(err_msg.format("GoalProgress Action Stats"), exc_info=1)

        try:
            # Generate scores for category progress for all users that have
            # selected one or more categories.
            for user in User.objects.filter(usercategory__isnull=False).distinct():
                objs = CategoryProgress.objects.generate_scores(user)
                cp_scores_count += objs.count()
            logger.info("Generated scores for CategoryProgress")
        except Exception:
            logger.error(err_msg.format("CategoryProgress"), exc_info=1)

        msg = (
            "Generating Progress Stats: {0} BehaviorProgress stats updated, "
            "{1} GoalProgress stats updated, {2} GoalProgress scores updated, "
            "{3} CategoryProgress scores updated."
        )
        self.stdout.write(
            msg.format(bp_count, gp_count, gp_scores_count, cp_scores_count)
        )
