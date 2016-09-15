"""
Our mobile app shows a feed of information to the user. This module compiles
that data, and exposes some utilities to construct that information.

"""
import pickle
import random

from collections import Counter
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import F, Q
from django.utils import timezone

import django_rq
from rewards.models import FunContent
from utils.dateutils import dates_range, format_datetime, weekday
from utils.user_utils import local_day_range

from .models import (
    DailyProgress,
    Goal,
    UserCompletedAction,
    UserCompletedCustomAction,
    UserGoal,
)

# Cache Keys.
TODAYS_ACTIONS = "todays_actions_{userid}"
TODAYS_ACTIONS_TIMEOUT = 30

FEED_DATA_KEY = "feed_data_{userid}"
FEED_DATA_TIMEOUT = 24 * 60 * 60  # 24 hours


# -----------------------------------------------------------------------------
# Feed Data Caching Technique.
# -----------------------------------------------------------------------------
# 1. We have a function that will pre-load the cache for all (relevant) users
#    (run by a cron job/ see the `cache_user_feed` managment command).
# 2. That function then stores the list of User IDs that it's cached data for.
# 3. We define a signal + handler that will invalidate & re-cache the feed data
#   TODO: ^^^ write this...
#   TODO: fire signal handler when a user (compeltes an action or adds a goal)
# -----------------------------------------------------------------------------

def cache_feed_data():
    """Call `feed_data` for some set of users. Doing so should populate the
    cache if it's not already cached.

    """
    User = get_user_model()

    # When we pre-cache this data, we'll store a SET of user IDs in Redis, so
    # we know whose data has been cached.
    CACHED_USERS = 'cached_users_feed'
    conn = django_rq.get_connection('default')

    cached_users = {int(x) for x in conn.smembers(CACHED_USERS)}
    users = User.objects.exclude(id__in=cached_users)

    cached_users = set()
    for user in users:
        feed_data(user)
        cached_users.add(user.id)

    # Reset the list of cached users.
    conn.sadd(CACHED_USERS, *cached_users)
    conn.expire(CACHED_USERS, FEED_DATA_TIMEOUT)


def feed_data(user):
    """Return a dict of all Feed Data for a given users.

    This function aggregates all of the data that's displayed in a users's
    feed into a single dict of content.

    """
    cache_key = FEED_DATA_KEY.format(userid=user.id)
    results = cache.get(cache_key)
    if results is not None:
        return pickle.loads(results)

    results = {
        'progress': None,
        'upcoming': [],
        'streaks': [],
        'suggestions': [],  # Note: Goal Suggestions. Currently disabled.
        'funcontent': None,
        'object_type': 'feed',
    }

    # Random FunContent objects.
    reward = FunContent.objects.random()
    results['funcontent'] = {
        'id': reward.id,
        'message': reward.message,
        'message_type': reward.message_type,
        'author': reward.author,
        'object_type': "funcontent"
    }

    # Progress for today
    results['progress'] = todays_progress(user)

    # Upcoming info (UserActions/CustomActions)
    upcoming_uas = todays_actions(user)
    upcoming_uas = upcoming_uas.values_list('id', flat=True)
    upcoming_uas = list(upcoming_uas)

    related = ('action', 'primary_goal', 'primary_category')
    useractions = user.useraction_set.select_related(*related)
    for ua in useractions.filter(id__in=upcoming_uas):
        primary_category = ua.get_primary_category()
        primary_goal = ua.get_primary_goal()
        results['upcoming'].append({
            'action_id': ua.id,
            'action': ua.action.title,
            'goal_id': primary_goal.id,
            'goal': primary_goal.title,
            'category_color': primary_category.color,
            'category_id': primary_category.id,
            'trigger': "{}".format(format_datetime(ua.next_reminder)),
            'type': 'useraction',
            'object_type': 'upcoming_item',
        })

    # Custom Actions
    upcoming_cas = todays_customactions(user)
    upcoming_cas = upcoming_cas.values_list('id', flat=True)
    upcoming_cas = list(upcoming_cas)

    related = ('customgoal', 'custom_trigger')
    customactions = user.customaction_set.select_related(*related)
    for ca in customactions.filter(id__in=upcoming_cas):
        results['upcoming'].append({
            'action_id': ca.id,
            'action': ca.title,
            'goal_id': ca.customgoal.id,
            'goal': ca.customgoal.title,
            'category_color': '#176CC4',
            'category_id': '-1',
            'trigger': "{}".format(format_datetime(ca.next_reminder)),
            'type': 'customaction',
            'object_type': 'upcoming_item',
        })

    # Sort upcoming data (UserActions/CustomActions) by trigger
    results['upcoming'] = sorted(results['upcoming'], key=lambda d: d['trigger'])

    # Streaks data
    results['streaks'] = progress_streaks(user)

    cache.set(cache_key, pickle.dumps(results), timeout=FEED_DATA_TIMEOUT)
    return results


def _fill_streaks(input_values, days):
    """This is a utility function that should fill in missing values for an
    ordered list of input values that contain a (datetime, int) tuple, keeping
    only the most recent number of days.

    NOTE: Input should already be ordered.

    """
    # NOTE: dates_range will generate dates up-to & including today (in UTC)
    # But these dates will not be tz-aware, so we want to add one and slice
    # off the last item in the list.
    desired_dates = sorted([dt.date() for dt in dates_range(days+1)])[-days:]

    # Insert zero-value items for any missing dates in the list.
    current_dates = [t[0] for t in input_values]
    for dt in desired_dates:
        if dt not in current_dates:
            input_values.append((dt, 0))
    input_values = sorted(input_values)  # now re-sort
    return input_values[-days:]  # Keep only the most recent "days" of values


def progress_streaks(user, days=7):
    """Find the given user's Action/CustomAction streaks (i.e. DailyProgress
    numbers for a given number of days)

    Returns a list of dicts containing the following:

    {
        'date': '2016-06-12',
        'day': 'Saturday',
        'count': 0,
    }

    """

    # Generate streaks data & add actions/customactions completed
    since = timezone.now() - timedelta(days=days)
    progresses = DailyProgress.objects.filter(user=user, created_on__gt=since)
    progresses = progresses.annotate(
        total=F('actions_completed') + F('customactions_completed')
    ).distinct().order_by("created_on")
    progresses = set(progresses.values_list('created_on', 'total'))
    progresses = sorted([(dt.date(), total) for dt, total in progresses])
    progresses = sorted(list(_fill_streaks(progresses, days=days)))

    results = []
    for date, count in progresses:
        results.append({
            'date': date,
            'day': weekday(date),
            'count': count,
            'object_type': 'feed_streak',
        })
    return results


def todays_customactions(user):
    """Return a queryset of CustomActions that are upcoming..."""
    today = local_day_range(user)  # start/end in UTC wrapping the user's day
    now = timezone.now()

    # Excluding those that have already been completed
    completed = user.usercompletedcustomaction_set.filter(
        updated_on__range=today,
        state=UserCompletedAction.COMPLETED)
    completed = completed.values_list('customaction', flat=True)
    upcoming_cas = user.customaction_set.filter(
        next_trigger_date__range=(now, today[1])
    )
    upcoming_cas = upcoming_cas.exclude(id__in=completed)
    upcoming_cas = upcoming_cas.order_by('next_trigger_date').distinct()
    return upcoming_cas


def todays_actions(user):
    """Return a QuerySet of *uncompleted* UserActions for today.

    Currently this is based on the UserAction.next_trigger_date field, and
    is not necessarily the list of notifications you will receive (because
    the number of notifications may be limited).

    This feed encompasses everything for the day, so you may see an "old"
    date associated with an Action.

    """
    cache_key = TODAYS_ACTIONS.format(userid=user.id)
    results = cache.get(cache_key)
    if results is not None:
        return results

    # We want to show only those left for "today" (in the user's timezone)
    today = local_day_range(user)  # start/end in UTC wrapping the user's day

    # FEED based on all of *today's* UserActions (next_trigger_date)
    cids = user.usercompletedaction_set.filter(
        updated_on__range=today,
        state=UserCompletedAction.COMPLETED
    )
    cids = cids.values_list("useraction", flat=True)

    # The `next_trigger_date` should always be saved as UTC
    upcoming = user.useraction_set.published().select_related('action')
    upcoming = upcoming.filter(next_trigger_date__range=today)
    upcoming = upcoming.exclude(id__in=cids)
    upcoming = upcoming.order_by('next_trigger_date')

    # Now cache for a short time because other functions here use this.
    cache.set(cache_key, upcoming, timeout=TODAYS_ACTIONS_TIMEOUT)
    return upcoming


def todays_customactions_progress(user):
    """Return some stats indicating to user's progress toward completing their
    custom actions that were scheduled for 'today'.

    * user -- the user for whom we're calculating stats.

    Returns a dict of the form (just like `todays_actions_progress`

        {
            'completed': X,
            'total': X,
            'progress': X,
        }

    where

    * completed is the number of CustomActions the user completed.
    * total is the total number of scheduled CustomActions
    * progress is an integer representing the percentage complete

    """
    # Start & End of "today", in UTC from the perspective of the user's timezone
    today = local_day_range(user)

    # Query for the items that should have been scheduled today PLUS
    # anything that actually got marked as completed today
    actions = UserCompletedCustomAction.objects.filter(
        updated_on__range=today,
        user=user
    )
    customaction_ids = actions.values_list('customaction', flat=True)

    # e.g. you've completed X / Y actions for today.
    completed = actions.filter(state=UserCompletedAction.COMPLETED).count()

    # NOTE: The `next_trigger_date` field gets refreshed automatically
    # every so often. So, to get a picture of the whole day at a time, we need
    # to consider both it and the previous trigger date.
    total = user.customaction_set.filter(
        Q(prev_trigger_date__range=today) |
        Q(next_trigger_date__range=today) |
        Q(id__in=customaction_ids)
    ).distinct().count()

    progress = 0
    if total > 0:
        progress = int(completed/total * 100)
    return {'completed': completed, 'total': total, 'progress': progress}


def todays_actions_progress(user):
    """Return some stats indicating to user's progress toward completing their
    actions that were scheduled for 'today'.

    Input:

    * user -- the user for whom we're calculating stats.

    Returns a dict of the form:

        {
            'completed': X,
            'total': X,
            'progress': X,
        }

    where

    * completed is the number of Actions the user completed.
    * total is the total number of scheduled actions
    * progress is an integer representing the percentage complete

    """
    # Start & End of "today", in UTC from the perspective of the user's timezone
    today = local_day_range(user)

    # Query for the UserActions that should have been scheduled today PLUS
    # anything that actually got marked as completed today
    ucas = UserCompletedAction.objects.filter(updated_on__range=today, user=user)
    useraction_ids = ucas.values_list('useraction', flat=True)

    # e.g. you've completed X / Y actions for today.
    completed = ucas.filter(state=UserCompletedAction.COMPLETED).count()

    # NOTE: The UserAction.next_trigger_date field gets refreshed automatically
    # every two hours. So, to get a picture of the whole day at a time, we need
    # to consider both it and the previous trigger date.
    # -------------------------------------------------------------------------
    # UPDATE: with the new UserQueue, there are things taht might ahve gotten
    # "scheduled" (e.g. next_trigger_date got set), but not queued up for GCM.
    # should we even count those? How fo fucking handle this :-/
    # -------------------------------------------------------------------------
    total = user.useraction_set.published().filter(
        Q(prev_trigger_date__range=today) |
        Q(next_trigger_date__range=today) |
        Q(id__in=useraction_ids)
    ).distinct().count()

    progress = 0
    if total > 0:
        progress = int(completed/total * 100)
    return {'completed': completed, 'total': total, 'progress': progress}


def todays_progress(user):
    """A combination of todays progress on Actions + Custom Actions + Enagement.
    This combines the results of the following:

    * todays_actions_progress
    * todays_customactions_progress
    * engagement_rank is a float that tells us how engaged the user has been
      over the past 15 days compared to other Compass users.
    * weekly_completions is the number of Actions / CustomActions that the user
      has completed in the past 7 days.

    """
    results = todays_actions_progress(user)
    custom = todays_customactions_progress(user)

    # Add the values together using a counter
    results = Counter(results)
    results.update(custom)

    # Include Engagment score
    results['engagement_rank'] = DailyProgress.objects.engagement_rank(user)

    # Completed tips in the past week.
    criteria = {
        'created_on__gte': timezone.now() - timedelta(days=7),
        'state': UserCompletedAction.COMPLETED,
    }
    ucas = user.usercompletedaction_set.filter(**criteria).count()
    uccas = user.usercompletedcustomaction_set.filter(**criteria).count()
    results['weekly_completions'] = ucas + uccas

    return dict(results)


def next_user_action(user):
    """Looks at all of the user's selected Actions, generating the 'next'
    trigger time and returns the upcoming action."""

    if not user.is_authenticated():
        return None
    return todays_actions(user).first()


def suggested_goals(user, limit=5):
    """Very dumb suggestions.

    * limit: Number of goals to return

    At the moment, it filters on Goals based on your feedback to the onboarding
    survey and the categories that you've selected (if any). If you don't match
    any of the set criteria, you'll receive random goal suggestions.

    This function excludes goals from Packaged content.

    """
    # XXX: Temporarily disabled suggestions.
    return []

    # From the goals the user has _not_ selected (that are public)...
    user_selected_goals = user.usergoal_set.values_list("goal__id", flat=True)
    goals = Goal.objects.published()  # excludes goals in packaged content
    goals = goals.exclude(id__in=user_selected_goals)

    cats = user.usercategory_set.filter(category__state='published')
    cats = cats.values_list('category', flat=True)

    # IF we've got sufficient number of categories, we can stick to the things
    # in the categories the user has chosen. If not, we'll just pull from
    # selected goals (otherwise there would be no suggestions)
    category_goals = goals.filter(categories__in=cats)
    if cats.count() and category_goals.count() > limit:
        goals = category_goals

    # Excluding the sensitive content
    goals = goals.exclude(keywords__contains=['sensitive']).distinct()

    # IF we have a large number of goals left over, use the use's profile data
    # to figure out which are most relevant. We'll pick from the following set:
    #
    # career, child, female, job, no_child, no_degree, no_job, no_relate,
    # relate, sensitive, tcijuniors, tciseniors, work
    profile = user.userprofile
    user_keywords = []
    exclude_keywords = []
    if goals.count() > limit * 2:

        if profile.has_degree:
            user_keywords.append('degree')
        else:
            user_keywords.append('no_degree')

        if profile.in_relationship:
            user_keywords.append('relate')
            exclude_keywords.append('no_relate')
        else:
            user_keywords.append('no_relate')
            exclude_keywords.append('relate')

        if profile.is_parent:
            user_keywords.append('child')
            exclude_keywords.append('no_child')
        else:
            user_keywords.append('no_child')
            exclude_keywords.append('child')

        if profile.employed:
            user_keywords.extend(['career', 'job', 'work'])
        else:
            user_keywords.append('no_job')

        if profile.sex and profile.sex.lower() == "female":
            user_keywords.append('female')

        # note: if user_keywords is empty, this result will be empty
        if len(user_keywords) > 0:
            goals = goals.filter(keywords__overlap=user_keywords)

    # But we always want to exclude female things for men.
    if profile.sex and profile.sex.lower() == "male":
        exclude_keywords.append('female')

    # note: excluding an empty list shouldn't change anything.
    goals = goals.exclude(keywords__overlap=exclude_keywords)

    # Pick a random sample of suggestions (or the leftover goals)...
    ids = list(goals.values_list("id", flat=True))
    if len(ids) > limit:
        goals = Goal.objects.filter(id__in=random.sample(ids, limit))
    else:
        goals = Goal.objects.filter(id__in=ids)

    return goals[:limit]


def _usergoal_sorter(usergoal):
    return usergoal.progress_value


def selected_goals(user):
    """Return the user's selected goals, ... ideally sorted in order of
    upcoming events, but that's a nasty query :(

    For now: Sorted by progress value (low-to-high)
    """
    user_goals = UserGoal.objects.published(user=user)
    user_goals = sorted(user_goals, key=_usergoal_sorter)
    return [(ug.progress_value, ug) for ug in user_goals]
