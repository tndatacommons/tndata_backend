from django.core.management.base import BaseCommand, CommandError
from userprofile.models import UserProfile


class Command(BaseCommand):
    """This command will reset all UserProfile.maximum_daily_notifications value
    to the given value, but ONLY those that are higher than what's given (if
    only one argument is given).

    If TWO arguments are provided, this command will replace all values
    matching the second with the first.

    """
    args = '<new_value> [old_value]'
    help = "Lower or change everyone's maximum_daily_notifications value."

    def handle(self, *args, **options):
        try:
            new_value = int(args[0])
            old_value = None
            if len(args) == 2:
                old_value = int(args[1])
        except (IndexError, ValueError):
            raise CommandError("One or two integer arguments are required.")

        if old_value is not None:
            # Find profiles matching the old value
            # and replace with the new value.
            updated = UserProfile.objects.filter(
                maximum_daily_notifications=old_value
            ).update(maximum_daily_notifications=new_value)
        else:
            # Find all profiles whose value is larger than the
            # new_value and replace with the new value.
            updated = UserProfile.objects.filter(
                maximum_daily_notifications__gt=new_value
            ).update(maximum_daily_notifications=new_value)

        msg = "\nReset {} profiles to '{}' max daily notifications"
        self.stdout.write(msg.format(updated, new_value))
