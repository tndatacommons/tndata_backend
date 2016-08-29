from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    """WARNING: This command will affect users' notifications.

    This command clears all existing data for the `UserAction.next_trigger_date`
    field. You can then re-populate it with `refresh_useractions`.

    """
    help = "Clear all values in UserAction.next_trigger_date. DESTRUCTIVE"

    def handle(self, *args, **options):
        resp = input("This will nullify the field. Are you sure? (y|n) > ")
        if resp.strip().lower() in ['y', 'yes']:
            cursor = connection.cursor()
            cursor.execute("UPDATE goals_useraction SET next_trigger_date=null")
            self.stdout.write("Ok, done.")
        else:
            self.stdout.write("Ok, cancelling.")


