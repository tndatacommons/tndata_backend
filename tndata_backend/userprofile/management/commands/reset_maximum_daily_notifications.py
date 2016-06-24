from django.core.management.base import BaseCommand, CommandError
from userprofile.models import UserProfile


class Command(BaseCommand):
    """This command will reset all UserProfile.maximum_daily_notifications value
    to the given value, but ONLY those that are higher than what's given.

    """
    args = '<new_value>'
    help = "Lower everyone's maximum_daily_notifications value."

    def handle(self, *args, **options):
        try:
            value = int(args[0])
        except (IndexError, ValueError):
            raise CommandError("An integar argument is required.")

        updated = UserProfile.objects.filter(
            maximum_daily_notifications__gt=value
        ).update(maximum_daily_notifications=value)

        self.stdout.write(
            "\nReset {} profiles to '{}' max daily notifications".format(
                updated, value)
        )
