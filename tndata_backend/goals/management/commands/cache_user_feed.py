from django.core.management.base import BaseCommand
from goals.user_feed import cache_feed_data


class Command(BaseCommand):
    """Pre-caches the user-feed (goals.user_feed.feed_data)."""

    help = "Pre-caches the user-feed (goals.user_feed.feed_data)."

    def handle(self, *args, **options):
        cache_feed_data()
