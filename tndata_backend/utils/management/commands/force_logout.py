from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'WARNING: Forces all users to logout. (kills all sessions, slowly)'

    def handle(self, *args, **options):
        """

        This coiuld be slow and ineffecient for a large number of users.
        We iterate over every session, clear it from the cache (because we're
        using cached_db sessions), then delete it from the DB.

        """
        engine = import_module(settings.SESSION_ENGINE)
        engine.SessionStore.clear_expired()  # Same as the clearsessions command

        count = 0
        for session in Session.objects.all():
            store = engine.SessionStore(session_key=session.session_key)
            store.flush()
            store.delete()
            session.delete()
            count += 1

        self.stdout.write("\nDeleted {} sessions.\n".format(count))
