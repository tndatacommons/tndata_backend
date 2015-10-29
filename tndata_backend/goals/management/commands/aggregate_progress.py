import logging

from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from goals.models import (
    BehaviorProgress,
    GoalProgress,
    CategoryProgress,
    UserBehavior
)

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = (
        'Update/creates BehaviorProgress, GoalProgress, & CategoryProgress. '
        'Run Nightly'
    )

    def handle(self, *args, **options):
        User = get_user_model()

        err_msg = "Failed to generate scores for {0}"
        bp_created = 0
        bp_count = 0
        gp_count = 0  # for aggregate action info

        gp_scores_count = 0  # for aggreage behavior info
        cp_scores_count = 0

        # BehaviorProgress was originally created _only_ when a user did the
        # daily checking. However, now that it's used to automatically aggregate
        # action completions, we need to create them automatically for the user
        # every day.
        today = timezone.now().date()
        for ub in UserBehavior.objects.all():
            try:
                bp = BehaviorProgress.objects.get(
                    user=ub.user,
                    user_behavior=ub,
                    reported_on__contains=today
                )
            except BehaviorProgress.DoesNotExist:
                # We need to create one.
                BehaviorProgress.objects.create(
                    user=ub.user,
                    user_behavior=ub,
                    status=BehaviorProgress.OFF_COURSE
                )
                bp_created += 1
            except (BehaviorProgress.MultipleObjectsReturned, Exception):
                pass

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
            # Re-calculate action progress stats, and daily/weekly/monthly
            # checkin values for GoalProgress objects over the history range in
            # which we're interested.
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
            "Generating Progress Stats: "
            "{0} BehaviorProgress created. "
            "{1} BehaviorProgress stats updated, "
            "{2} GoalProgress stats updated, "
            "{3} GoalProgress scores updated, "
            "{4} CategoryProgress scores updated."
        )
        self.stdout.write(
            msg.format(bp_created, bp_count, gp_count, gp_scores_count, cp_scores_count)
        )
