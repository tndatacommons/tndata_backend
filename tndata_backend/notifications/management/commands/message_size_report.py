import array
import statistics
from django.core.management.base import BaseCommand
from notifications.models import GCMMessage


class Command(BaseCommand):
    help = 'Print some info about push notification payload sizes'

    def handle(self, *args, **options):
        sizes = array.array('L')

        for msg in GCMMessage.objects.all():
            # Store the size of the gcm payload for existing messages.
            # The json-encoded string *should* be in the correct text encoding
            sizes.append(len(msg.content_json))

        # Do some reporting.
        sizes = sorted(sizes)
        print("\n-------------------------------------------------------")
        print("For current notifications:")
        print("- Mean: {} bytes".format(round(statistics.mean(sizes), 2)))
        print("- Median: {} bytes".format(round(statistics.median(sizes), 2)))
        print("- Mode: {} bytes".format(round(statistics.median(sizes), 2)))
        print("- Stdev: {}".format(round(statistics.stdev(sizes), 2)))
        print("- Smallest: {} bytes".format(min(sizes)))
        print("- Largest: {} bytes".format(max(sizes)))
        print("-------------------------------------------------------\n")
