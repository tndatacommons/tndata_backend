from datetime import datetime
from django.core.management.base import NoArgsCommand

from notifications import GCMMessage


class Command(NoArgsCommand):
    help = 'Sends messages to GCM'

    def handle_noargs(self, **options):
        delivery_date = datetime.utcnow()

        # Look for all the undelivered/non-errored messages.
        messages = GCMMessage.objects.exclude(success=True)
        messages = messages.filter(
            deliver_on__gte=delivery_date,
            success=None
        )
        for message in messages:
            message.send()
