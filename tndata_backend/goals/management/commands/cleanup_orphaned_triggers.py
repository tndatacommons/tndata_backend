from django.core.management.base import BaseCommand
from goals.models import Trigger


class Command(BaseCommand):
    """Remove triggers that aren't being used. This command checks for these
    conditions:

    1. Trigger has no user
    2. Trigger has no set of UserActions
    3. Trigger has no set of CustomActions
    4. Is not one of the default Action triggers

    """
    help = 'Removes orphan Trigger data'

    def handle(self, *args, **options):
        triggers = Trigger.objects.filter(
            user__isnull=True,
            action_default__isnull=True,
            useraction__isnull=True,
            customaction__isnull=True
        )

        # Count & remove.
        num = triggers.count()
        triggers.delete()

        self.stdout.write("Removed {} triggers.\n".format(num))
