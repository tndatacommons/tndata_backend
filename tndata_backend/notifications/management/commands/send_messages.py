import logging
import waffle

from django.core.management.base import BaseCommand
from notifications.models import GCMMessage


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sends messages to GCM'

    def handle(self, *args, **options):
        # NOTE: IF this switch is active, we rely on rq-scheduler to deliver
        # notifications; otherwise, this script runs periodically and will
        # query for items that need to be delivered (directly from GCMMessages)
        if waffle.switch_is_active('use-rqscheduler'):
            self.stderr.write("This command has been deprecated")
        else:
            # Look for all the undelivered/non-errored messages.
            messages = GCMMessage.objects.ready_for_delivery()
            if messages.exists():
                log_msg = "Sending {0} GCMMessages".format(messages.count())
                logger.info(log_msg)
                self.stdout.write("{0}\n".format(log_msg))

                for message in messages:
                    try:
                        message.send()
                        log_message = "Sent to GCM: user: {0}, message: {1}".format(
                            message.user.id, message.message
                        )
                        logger.info(log_message)
                    except Exception:
                        log_msg = "Failed to send GCMMEssage id = {0}".format(message.id)
                        logger.error(log_msg)
                        self.stdout.write("{0}\n".format(log_msg))

                logger.info("Finished Sending GCM Notifications")
                self.stdout.write("Finished Sending GCM Notifications")
