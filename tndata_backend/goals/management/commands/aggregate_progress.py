from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from goals.models import GoalProgress, CategoryProgress


class Command(BaseCommand):
    help = 'Creates GoalProgress and CategoryProgress objects. Run Nightly'

    def handle(self, *args, **options):
        User = get_user_model()
        # Generate scores for progress toward goals...
        for user in User.objects.filter(usergoal__isnull=False).distinct():
            GoalProgress.objects.generate_scores(user)

        # ...and toward categories.
        for user in User.objects.filter(usercategory__isnull=False).distinct():
            CategoryProgress.objects.generate_scores(user)
