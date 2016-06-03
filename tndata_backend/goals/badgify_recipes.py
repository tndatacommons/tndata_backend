"""
Badgify Recipes.

See: https://github.com/ulule/django-badgify

----

Typical workflow for best performances

$ python manage.py badgify_sync badges
$ python manage.py badgify_sync awards --disable-signals
$ python manage.py badgify_sync counts

----

TODO: Ideas for implementing this:

1. Create recipes as part of the goals app.
2. Cron jobs taht will run the badgify_sync commands to do awards
3. ^ listen for signals (Award.post_save?) and send a push notification when
   a user is awarded a badge. (wrap this in a waffle.switch)
4. New app (badge_api?) that exposes a user's awarded badges

----

NOTE: on Recipes; A recipe class must implement:

_ name class attribute
    The badge name (humanized).
- image property
    The badge image/logo as a file object.

Optionally, A recipe class may implement:

- slug class attribute
    The badge slug (used internally and in URLs). If not provided, it
    will be auto-generated based on the badge name.
- description class attribute
    The badge description (short). It not provided, value will be blank.
- user_ids property
    QuerySet returning User IDs likely to be awarded. You must return a
    QuerySet and not just a Python list or tuple. You can use
    values_list('id', flat=True).
- db_read class attribute
    The database alias on which to perform read queries. Defaults to
    django.db.DEFAULT_DB_ALIAS.
- batch_size class attribute
    How many Award objects to create at once. Defaults to
    BADGIFY_BATCH_SIZE (500).

"""
from datetime import timedelta
from django.contrib.staticfiles.storage import staticfiles_storage

from badgify.recipe import BaseRecipe
import badgify

from django.contrib.auth import get_user_model
from django.utils import timezone


# ----------------
# Helper functions
# ----------------

def just_joined(minutes=10, days=None):
    """Return a QuerySet (a ValuesListQuerySet, actually) of users who've just
    joined within the past `minutes` (or `days`))"""
    User = get_user_model()
    if days:
        since = timezone.now() - timedelta(days=days)
    else:
        since = timezone.now() - timedelta(minutes=minutes)
    return User.objects.filter(date_joined__gte=since).values_list("id", flat=True)


def just_logged_in(nth, minutes=10):
    """Return a QuerySet (a ValuesListQuerySet) of users who've logged in for
    the `nth` time (within the past few `minutes`)."""
    User = get_user_model()
    since = timezone.now() - timedelta(minutes=minutes)
    users = User.objects.filter(last_login__gte=since, userprofile__app_logins=nth)
    return users.values_list("id", flat=True)


# -------------------------
# General App-usage recipes
# -------------------------

class StarterRecipe(BaseRecipe):
    """Awarded when signing up (hopefully about the time they view the feed)."""
    name = 'Starter'
    slug = 'starter'
    description = "Congrats on signing up! You're on your way to success!"

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        """Returns a queryset of users who joined within the past 10 minutes"""
        return just_joined(minutes=10)

badgify.register(StarterRecipe)


class ExplorerRecipe(BaseRecipe):
    """Awarded when the user has been signed up for a week."""
    name = 'Explorer'
    slug = 'explorer'
    description = "You've used Compass for a week! Woo-hoo!"

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        return just_joined(days=7)

badgify.register(ExplorerRecipe)


class LighthouseRecipe(BaseRecipe):
    """Awarded when the user has been signed up for a month."""
    name = 'Lighthouse'
    slug = 'lighthouse'
    description = "You've used Compass for a month! Woo-hoo!"

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        return just_joined(days=30)

badgify.register(LighthouseRecipe)


class HomecomingRecipe(BaseRecipe):
    """Awarded by coming back to the app a second time."""
    name = 'Homecoming'
    slug = 'homecoming'
    description = "Congrats for coming back."

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        return just_logged_in(2)

badgify.register(HomecomingRecipe)


class SeekerRecipe(BaseRecipe):
    """Awarded by coming back to the app (a third time)"""
    name = 'Seeker'
    slug = 'seeker'
    description = "Congrats for coming back the third time."

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        return just_logged_in(3)

badgify.register(SeekerRecipe)


class PathfinderRecipe(BaseRecipe):
    """Awarded by coming back to the app (a seventh time)"""
    name = 'Pathfinder'
    slug = 'pathfinder'
    description = "Congrats for coming back the seventh time."

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        return just_logged_in(7)

badgify.register(PathfinderRecipe)


class NavigatorRecipe(BaseRecipe):
    """Awarded by coming back to the app (a 14th time)"""
    name = 'Navigator'
    slug = 'navigator'
    description = "Congrats for coming back the fourteenth time."

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        return just_logged_in(14)

badgify.register(NavigatorRecipe)


# TODO: Scout -- After leaving the "total badges" activities
# ----------------------------------------------------------
# class ScoutRecipe(BaseRecipe):
#     """Awarded by coming back to the app (a 14th time)"""
#     name = 'Scout'
#     slug = 'scout'
#     description = "You're awesome for checking your stats!"
#
#     @property
#     def image(self):
#         return staticfiles_storage.open('badges/placeholder.png')
#
#     @property
#     def user_ids(self):
#         # TODO: How to do this?
#
# badgify.register(NavigatorRecipe)
