from django.core.management.base import BaseCommand
from notifications.models import GCMMessage


class Command(BaseCommand):
    help = 'Sends messages to GCM'

    def handle(self, *args, **options):
        # Look for all the undelivered/non-errored messages.
        for message in GCMMessage.objects.ready_for_delivery():
            message.send()
