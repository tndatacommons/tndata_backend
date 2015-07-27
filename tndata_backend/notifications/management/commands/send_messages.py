import logging

from django.core.management.base import BaseCommand
from notifications.models import GCMMessage
from utils import slack


logger = logging.getLogger("loggly_logs")

# user.email -> slack username
slack_users = {
    'brad@brad.tips': 'bkmontgomery',
    'ringram@tndata.org': 'ringram',
    'ismaha91@gmail.com': 'ialonso',
}


class Command(BaseCommand):
    help = 'Sends messages to GCM'

    def handle(self, *args, **options):
        # Look for all the undelivered/non-errored messages.
        messages = GCMMessage.objects.ready_for_delivery()
        if messages.exists():
            log_msg = "Sending {0} GCMMessages".format(messages.count())
            logger.info(log_msg)
            self.stdout.write("{0}\n".format(log_msg))

            for message in messages:
                try:
                    message.send()

                    # --- Temporary debegging via Slack -----------------------
                    # For some of our messages, we want to send a PM to the
                    # user that their message was sent up to GCM.
                    slack_user = slack_users.get(message.user.email)
                    if slack_user is not None:
                        slack_message = "Queued Notification on GCM: {0}".format(
                            message.message
                        )
                        slack.post_private_message(slack_user, slack_message)
                    # ---------------------------------------------------------

                except Exception:
                    log_msg = "Failed to send GCMMEssage id = {0}".format(message.id)
                    logger.error(log_msg)
                    self.stdout.write("{0}\n".format(log_msg))

            logger.info("Finished Sending GCM Notifications")
            self.stdout.write("Finished Sending GCM Notifications")
