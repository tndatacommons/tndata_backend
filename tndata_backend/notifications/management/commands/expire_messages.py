import logging

from django.core.management.base import BaseCommand
from notifications.models import GCMMessage


logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Removes messages that have already been delivered'

    def handle(self, *args, **options):
        qs = GCMMessage.objects.expired()
        msg = "Expired {0} GCM Messages".format(qs.count())
        qs.delete()

        logger.info(msg)
