import logging
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chat.models import ChatMessage
from notifications import sms
from utils.datastructures import flatten

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# NOTE: This will pretty aggressively send out notifications at all times of
#       of the day or night if there are ChatMessages. To combat that, we
#       should schedule this command during certain hours only, e.g.
#
#       Something like:
#
#           Every 15 minutes between the hours of 8am and 18 (6pm) CST.
#           http://corntab.com/?c=*/15_8-18_*_*_*
#
# -----------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Sends a notification (currently SMS) to a user who's received "
        "'recent' chat messages. Schedule this to run frequently."
    )

    def handle(self, *args, **options):
        User = get_user_model()

        # Get all the users that probably have messages.
        # (we don't save the recipient's ID in the message so this is a hack)
        user_ids = flatten(
            room.split('-')[1:] for room in
            ChatMessage.objects.recent().values_list('room', flat=True)
        )

        # filter out those who don't have a listed phone number
        users = User.objects.filter(id__in=user_ids, userprofile__phone__gt='')

        # Now make sure we have them in a numbers-only format.
        numbers = users.values_list('userprofile__phone', flat=True)
        message = (
            "You have new messages!\n"
            "View them at http://officehours.tndata.org"
        )
        sms.mass_send(numbers, message, topic_name="ChatNotifications")
