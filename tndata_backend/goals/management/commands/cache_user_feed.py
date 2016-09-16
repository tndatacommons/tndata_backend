from django.core.management.base import BaseCommand
from goals.user_feed import cache_feed_data

import waffle


class Command(BaseCommand):
    """Pre-caches the user-feed (goals.user_feed.feed_data)."""

    help = "Pre-caches the user-feed (goals.user_feed.feed_data)."

    def handle(self, *args, **options):
        if waffle.switch_is_active("cache-user-feed"):
            cache_feed_data()
