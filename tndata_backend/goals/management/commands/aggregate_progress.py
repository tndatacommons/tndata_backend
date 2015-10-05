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

        try:
            # Update BehaviorProgress instances in some time period, so they
            # re-calculate stats for completed actions
            date = timezone.now() - timedelta(days=settings.PROGRESS_HISTORY_DAYS)
            for bp in BehaviorProgress.objects.filter(reported_on__gte=date):
                bp.save()  # Calls BehaviorProgress._calculate_action_progress
        except Exception:
            logger.error(err_msg.format("BehaviorProgress"), exc_info=1)

        try:
            # Generate scores for goal progress for all users that have
            # selected one or more Goals.
            for user in User.objects.filter(usergoal__isnull=False).distinct():
                GoalProgress.objects.generate_scores(user)
            logger.info("Generated scores for GoalProgress")
        except Exception:
            logger.error(err_msg.format("GoalProgress"), exc_info=1)

        try:
            # Generate scores for category progress for all users that have
            # selected one or more categories.
            for user in User.objects.filter(usercategory__isnull=False).distinct():
                CategoryProgress.objects.generate_scores(user)
            logger.info("Generated scores for CategoryProgress")
        except Exception:
            logger.error(err_msg.format("CategoryProgress"), exc_info=1)
