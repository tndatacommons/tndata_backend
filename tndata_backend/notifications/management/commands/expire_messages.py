from django.core.management.base import BaseCommand
from notifications.models import GCMMessage


class Command(BaseCommand):
    help = 'Removes messages that have already been delivered'

    def handle(self, *args, **options):
        GCMMessage.objects.expired().delete()
