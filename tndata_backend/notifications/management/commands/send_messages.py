import logging

from django.core.management.base import BaseCommand
from notifications.models import GCMMessage


logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Sends messages to GCM'

    def handle(self, *args, **options):
        # Look for all the undelivered/non-errored messages.
        messages = GCMMessage.objects.ready_for_delivery()
        logger.info("Sending {0} GCMMessages".format(messages.count()))
        for message in messages:
            try:
                message.send()
            except Exception:
                logger.error("Failed to send GCMMEssage id = %s", message.id)
