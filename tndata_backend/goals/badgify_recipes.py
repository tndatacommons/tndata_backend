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

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils import timezone

from badgify.recipe import BaseRecipe
import badgify

from .models import DailyProgress

from utils import dateutils


# ----------------
# Helper functions
# ----------------

def just_joined(minutes=10, days=None):
    """Return a QuerySet (a ValuesListQuerySet, actually) of users who've just
    joined within the past `minutes` (or `days`))"""
    User = get_user_model()
    if days:
        since = timezone.now() - timedelta(days=days)
    elif minutes:
        since = timezone.now() - timedelta(minutes=minutes)
    else:
        return User.objects.none()
    return User.objects.filter(date_joined__gte=since).values_list("id", flat=True)


def just_logged_in(nth, minutes=10):
    """Return a QuerySet (a ValuesListQuerySet) of users who've logged in for
    the `nth` time (within the past few `minutes`)."""
    User = get_user_model()
    since = timezone.now() - timedelta(minutes=minutes)
    users = User.objects.filter(last_login__gte=since, userprofile__app_logins=nth)
    return users.values_list("id", flat=True)


def checkin_streak(streak_number, badge_slug):
    """Return a queryset of Users that have the a checkin-streak of
    `streak_number`, but have not received this specified badge, yet."""
    User = get_user_model()

    today = dateutils.date_range(timezone.now())
    user_ids = DailyProgress.objects.filter(
        created_on__range=today,
        checkin_streak=streak_number
    ).values_list("user", flat=True).distinct()

    users = User.objects.filter(pk__in=user_ids)
    users = users.exclude(badges__badge__slug=badge_slug).distinct()
    return users


# -------------------------
# General App-usage recipes
# -------------------------

class SignupMixin:
    minutes_since_signup = None
    days_since_signup = None
    badge_path = 'badges/placeholder.png'

    @property
    def image(self):
        return staticfiles_storage.open('badges/placeholder.png')

    @property
    def user_ids(self):
        """Returns a queryset of users who joined within the past 10 minutes"""
        return just_joined(
            minutes=self.minutes_since_signup,
            days=self.days_since_signup
        )


class StarterRecipe(SignupMixin, BaseRecipe):
    """Awarded when signing up (hopefully about the time they view the feed)."""
    name = 'Starter'
    slug = 'starter'
    description = "Congrats on signing up! You're on your way to success!"
    badge_path = 'badges/placeholder.png'
    minutes_since_singup = 10
badgify.register(StarterRecipe)


class ExplorerRecipe(SignupMixin, BaseRecipe):
    """Awarded when the user has been signed up for a week."""
    name = 'Explorer'
    slug = 'explorer'
    description = "You've used Compass for a week! Woo-hoo!"
    badge_path = 'badges/placeholder.png'
    days_since_signup = 7
badgify.register(ExplorerRecipe)


class LighthouseRecipe(BaseRecipe):
    """Awarded when the user has been signed up for a month."""
    name = 'Lighthouse'
    slug = 'lighthouse'
    description = "You've used Compass for a month! Woo-hoo!"
    badge_path = 'badges/placeholder.png'
    days_since_signup = 30
badgify.register(LighthouseRecipe)


class LoginMixin:
    minutes_since_login = None
    login_number = None
    badge_path = 'badges/placeholder.png'

    @property
    def image(self):
        return staticfiles_storage.open(self.badge_path)

    @property
    def user_ids(self):
        since = self.minutes_since_login or 10
        return just_logged_in(self.login_number, minutes=since)


class HomecomingRecipe(LoginMixin, BaseRecipe):
    """Awarded by coming back to the app a second time."""
    name = 'Homecoming'
    slug = 'homecoming'
    description = "Congrats for coming back."
    badge_path = 'badges/placeholder.png'
    login_number = 2
badgify.register(HomecomingRecipe)


class SeekerRecipe(BaseRecipe):
    """Awarded by coming back to the app (a third time)"""
    name = 'Seeker'
    slug = 'seeker'
    description = "Congrats for coming back the third time."
    badge_path = 'badges/placeholder.png'
    login_number = 3
badgify.register(SeekerRecipe)


class PathfinderRecipe(BaseRecipe):
    """Awarded by coming back to the app (a seventh time)"""
    name = 'Pathfinder'
    slug = 'pathfinder'
    description = "Congrats for coming back the seventh time."
    login_number = 7
badgify.register(PathfinderRecipe)


class NavigatorRecipe(BaseRecipe):
    """Awarded by coming back to the app (a 14th time)"""
    name = 'Navigator'
    slug = 'navigator'
    description = "Congrats for coming back the fourteenth time."
    login_number = 14
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


# ------------------------------
# Self-report / Check-in recipes
# ------------------------------

class CheckinMixin:
    badge_path = 'badges/placeholder.png'  # Path to the badge.
    checkin_days = 1  # Number days in a row the user has checked in.

    @property
    def image(self):
        return staticfiles_storage.open(self.badge_path)

    @property
    def user_ids(self):
        return checkin_streak(self.checkin_days, self.slug)


class ThoughtfulRecipe(CheckinMixin, BaseRecipe):
    name = 'Thoughtful'
    slug = 'thoughtful'
    description = "This was your first time checking in! You're awesome!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 1
badgify.register(ThoughtfulRecipe)


class ConscientiousRecipe(CheckinMixin, BaseRecipe):
    name = 'Conscientious'
    slug = 'conscientious'
    description = "This was your second time checking in! You're taking care of yourself!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 2
badgify.register(ConscientiousRecipe)


class StreakThreeDaysRecipe(BaseRecipe):
    name = 'Streak - three days!'
    slug = 'streak-three-days'
    description = "You've checked in three times in a row! Score!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 3
badgify.register(StreakThreeDaysRecipe)


class StreakFiveDaysRecipe(BaseRecipe):
    name = 'Streak - five days!'
    slug = 'streak-five-days'
    description = "You've checked in five times in a row! Way to go!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 3
badgify.register(StreakFiveDaysRecipe)


class StreakOneWeekRecipe(BaseRecipe):
    name = 'Streak - one week!'
    slug = 'streak-one-week'
    description = "You've checked in seven times in a row! Keep up the streak!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 7
badgify.register(StreakOneWeekRecipe)


class StreakTwoWeeksRecipe(BaseRecipe):
    name = 'Streak - two weeks!'
    slug = 'streak-two-weeks'
    description = "You've checked in every day for two weeks! Score!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 14
badgify.register(StreakTwoWeeksRecipe)


class StreakThreeWeeksRecipe(BaseRecipe):
    name = 'Streak - three weeks!'
    slug = 'streak-three-weeks'
    description = "You've checked in every day for three weeks! Score!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 21
badgify.register(StreakThreeWeeksRecipe)


class StreakFourWeeksRecipe(BaseRecipe):
    name = 'Streak - four weeks!'
    slug = 'streak-four-weeks'
    description = "You've checked in every day for four weeks! Score!"
    badge_path = 'badges/placeholder.png'
    checkin_days = 28
badgify.register(StreakFourWeeksRecipe)
