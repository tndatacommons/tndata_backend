import logging

from django.core.management.base import BaseCommand
from goals.models import CustomAction, UserAction

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Updates the next_trigger_date field for stale UserActions and CustomActions.'

    def handle(self, *args, **options):
        count = 0
        for ua in UserAction.objects.stale():
            count += 1
            ua.save(update_triggers=True)  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} UserActions".format(count)
        logger.error(msg)
        self.stderr.write(msg)

        count = 0
        for ca in CustomAction.objects.stale():
            count += 1
            ca.save()  # fields get refreshed on save.

        msg = "Refreshed Trigger Date for {0} CustomActions".format(count)
        logger.error(msg)
        self.stderr.write(msg)
