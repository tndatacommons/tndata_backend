import logging

from django.core.management.base import BaseCommand
from goals.models import UserAction

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Updates the UserAction.next_trigger_date field for stale entries.'

    def handle(self, *args, **options):
        count = 0
        for ua in UserAction.objects.stale():
            count += 1
            ua.save()  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} UserActions".format(count)
        logger.error(msg)
        self.stderr.write(msg)
