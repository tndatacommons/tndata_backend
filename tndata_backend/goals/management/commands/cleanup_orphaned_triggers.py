from django.core.management.base import BaseCommand
from django.utils.text import slugify

from goals.models import Trigger
from goals.settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_MORNING_GOAL_TRIGGER_NAME,
    DEFAULT_EVENING_GOAL_TRIGGER_NAME,
)


class Command(BaseCommand):
    """Remove triggers that aren't being used. This command checks for three
    conditions:

    1. Trigger has no user
    2. Trigger is not a default trigger for an Action
    3. Trigger has no set of UserActions
    4. Trigger has no set of CustomActions
    4. Is not one of the default Behavior triggers (morning/evening check-in)

    """
    help = 'Removes orphan Trigger data'

    def handle(self, *args, **options):

        # Slugs for the default behavior & morning/evening checkins
        default_slugs = [
            slugify(DEFAULT_BEHAVIOR_TRIGGER_NAME),
            slugify(DEFAULT_MORNING_GOAL_TRIGGER_NAME),
            slugify(DEFAULT_EVENING_GOAL_TRIGGER_NAME),
        ]

        triggers = Trigger.objects.exclude(name_slug__in=default_slugs).filter(
            user__isnull=True,
            action_default__isnull=True,
            useraction__isnull=True,
            customaction__isnull=True
        )

        # Count & remove.
        num = triggers.count()
        triggers.delete()

        self.stdout.write("Removed {} triggers.\n".format(num))
