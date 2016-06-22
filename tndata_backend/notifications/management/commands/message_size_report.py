import array
import json
import statistics
import sys

from django.core.management.base import BaseCommand

from notifications.models import GCMMessage


class Command(BaseCommand):
    help = 'Print some info about message sizes'

    def handle(self, *args, **options):
        sizes = array.array('L')
        expanded_sizes = array.array('L')

        for msg in GCMMessage.objects.all():
            # Store the size of the gcm payload for existing messages.
            sizes.append(sys.getsizeof(msg.content_json))

            # Then investigate including more info (e.g. embedding the action
            # and behavior), and check on the resulting size.
            if msg.content_object and msg.content_type and msg.content_type.name.lower() == "action":
                payload = msg.content
                action = msg.content_object
                payload['action'] = {
                    'id': action.id,
                    'title': action.title,
                    'description': action.description,
                }
                payload['behavior'] = {
                    'id': action.behavior_id,
                    'title': action.behavior.title,
                    'description': action.behavior.description,
                }
                payload = json.dumps(payload)
                expanded_sizes.append(sys.getsizeof(payload))

        # Do some reporting.
        sizes = sorted(sizes)
        print("\n-------------------------------------------------------")
        print("For current notifications:")
        print("- Mean: {} bytes".format(statistics.mean(sizes)))
        print("- Median: {} bytes".format(statistics.median(sizes)))
        print("- Mode: {} bytes".format(statistics.median(sizes)))
        print("- Stdev: {}".format(statistics.stdev(sizes)))
        print("- Smallest: {} bytes".format(min(sizes)))
        print("- Largest: {} bytes".format(max(sizes)))

        sizes = sorted(expanded_sizes)
        print("\nIncluding Action/Behavior dataa within the message:")
        print("- Mean: {} bytes".format(statistics.mean(sizes)))
        print("- Median: {} bytes".format(statistics.median(sizes)))
        print("- Mode: {} bytes".format(statistics.median(sizes)))
        print("- Stdev: {}".format(statistics.stdev(sizes)))
        print("- Smallest: {} bytes".format(min(sizes)))
        print("- Largest: {} bytes".format(max(sizes)))
        print("-------------------------------------------------------\n")
