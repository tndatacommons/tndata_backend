import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from goals.models import GoalProgress, CategoryProgress


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates GoalProgress and CategoryProgress objects. Run Nightly'

    def handle(self, *args, **options):
        User = get_user_model()

        # Generate scores for progress toward goals...
        try:
            for user in User.objects.filter(usergoal__isnull=False).distinct():
                GoalProgress.objects.generate_scores(user)
            logger.info("Generated scores for GoalProgress")
        except Exception:
            logger.error("Failed to generate scores for GoalProgress", exc_info=1)
        # ...and toward categories.
        try:
            for user in User.objects.filter(usercategory__isnull=False).distinct():
                CategoryProgress.objects.generate_scores(user)
            logger.info("Generated scores for CategoryProgress")
        except Exception:
            logger.error("Failed to generate scores for CategoryProgress", exc_info=1)
