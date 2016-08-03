from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cronlog.models import CronLog


class Command(BaseCommand):
    """Clear old CronLog instances so we don't fill up our database."""
    help = 'Removes old CronLog instances'

    def handle(self, *args, **options):
        dt = timezone.now() - timedelta(days=5)
        deleted = CronLog.objects.filter(created_on__lte=str(dt)).delete()
        self.stdout.write("Removed {} CronLog objects.\n".format(deleted or 0))
