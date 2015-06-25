import logging

from django.core.management.base import BaseCommand
from notifications.models import GCMMessage
from utils import slack

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Sends messages to GCM'

    def handle(self, *args, **options):
        # Look for all the undelivered/non-errored messages.
        messages = GCMMessage.objects.ready_for_delivery()
        log_msg = "Sending {0} GCMMessages".format(messages.count())
        logger.info(log_msg)
        self.stdout.write("{0}\n".format(log_msg))
        for message in messages:
            try:
                message.send()
                m = "Sending GCM Message ({0}): {1}".format(
                    message.id, message.title
                )
                slack.post_message("#tech", m)
            except Exception:
                log_msg = "Failed to send GCMMEssage id = {0}".format(message.id)
                logger.error(log_msg)
                self.stdout.write("{0}\n".format(log_msg))

        logger.error("Finished Sending GCM Notifications")
        self.stdout.write("Finished Sending GCM Notifications")
