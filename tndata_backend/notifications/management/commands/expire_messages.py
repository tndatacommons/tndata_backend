import logging
from django.core.management.base import BaseCommand
from notifications.models import GCMMessage
from utils import slack

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Removes messages that have already been delivered'

    def handle(self, *args, **options):
        qs = GCMMessage.objects.expired()
        if qs.exists():
            for msg in qs:
                slack.log_message(msg, "Deleting Message")
            msg = "Expired {0} GCM Messages".format(qs.count())
            # Delete those expired messages.
            qs.delete()
            logger.info(msg)
