"""
TODO: WIP - A feed of relevant content for the user.

Our mobile app shows a feed of information to the user. This module compiles
that data, and exposes some utilities to construct that information.

Some possible data in the user's feed:

- Up Next: The Action that is up next for the user.
- Progress: Provide some sort of information regarding their progress toward
  selected goals (possibly related to the action that is _up next_).
- Suggested Goals: If a user has no (or _few_) selected goals, give them a few
  suggestions based on their selected categories and/or demographics
- Selected Goals: All of the user's selected Goals.


See this trello card for more details:
https://trello.com/c/zKedLoZe/170-initial-home-feed

"""
import random

from datetime import timedelta
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from utils.user_utils import local_day_range

from .models import Goal, UserCompletedAction


# Some Cache keys.
TODAYS_ACTIONS = "todays_actions_{userid}"
TODAYS_ACTIONS_TIMEOUT = 30


def action_feedback(user, useraction, lookback=30):
    """This function assembles data for *feedback* on the user's upcoming
    action. See: https://goo.gl/7UUjzq

    This is essentially just a bit of encouragment for the user, but the content
    of that encouragement is based on their previous activity. Roughly:

    - If <= 20% of the current months previously scheduled actions completed
      (i.e., 2 actions each day. On the 10th day of the month if <= 4 actions
      completed)
    - If > 20% but <= 60% of the current months previously scheduled actions
      completed (i.e., 2 actions each day. On the 10th day of the month if > 4
      but <= 12 actions completed)
    - If > 60% of the current months previously scheduled actions completed
      (i.e., 2 actions each day. On the 10th day of the month if > 12 actions
      completed)

    Parameters:

    * user - the user for which this data is assembled.
    * useraction - the user's next action (a UserAction instance)
    * lookback - number of days to look back for their completed history.

    Returns a dict of the form:

        {
            'title': 'some string',
            'subtitle': 'some string',
            'total': <total number of activities>,
            'completed': <number completed>,
            'percentage': <percentage: completed / total>,
            'icon': <integer value 1-4>
        }

    """
    feedback = {
        'low': {
            'title': "I've done some work to {goal} this month!",
            'subtitle': 'Even small steps can help me reach my goal',
            'icon': 1,
        },
        'med': {
            'title': "I've done {num} activities to {goal} this month!",
            'subtitle': 'I must really want this!',
            'icon': 2,
        },
        'hi': {
            'title': (
                "I've done {num} out of {total} activities to {goal} "
                "this month!"
            ),
            'subtitle': "I'm doing great! I'll schedule another activity!",
            'icon': 3,
        },
    }
    # Data points needed:
    # - total number of UserActions for the time period
    # - completed UserActions for the time period.
    # - percentage of Actions completed/scheduled in some period (lookback)
    # - icons indicate which icon in the app should be displayed:
    #   1: footsteps, 2: thumbs-up, 3: ribbon, 4: trophy (when all are completed)

    # NOTE: UserAction's always get updated with the *next up* trigger date
    # so we can't use them to calculate the above. For now, we'll just use
    # the UserCompletedAction model, but that will only work if the user has
    # the version of the app that records incomplete as well as completed actions.
    dt = timezone.now() - timedelta(days=lookback)
    qs = UserCompletedAction.objects.filter(
        user=user,
        useraction=useraction,
        updated_on__gt=dt
    )
    total = qs.count()
    completed = qs.filter(state="completed").count()
    if total > 0:
        percentage = round((completed / total) * 100)
    else:
        percentage = 0
    goal = useraction.get_primary_goal()
    if goal:
        goal_title = goal.title.lower()
    else:
        goal_title = "achieve my goal"

    resp = {
        'title': '',
        'subtitle': '',
        'total': total,
        'completed': completed,
        'incomplete': total - completed,
        'percentage': percentage,
        'icon': 1,
    }

    if percentage <= 20:
        title = feedback['low']['title'].format(goal=goal_title)
        resp.update({
            'title': title,
            'subtitle': feedback['low']['subtitle'],
            'icon': feedback['low']['icon'],
        })
    elif percentage >= 60:
        title = feedback['hi']['title'].format(
            goal=goal_title, num=completed, total=total
        )
        resp.update({
            'title': title,
            'subtitle': feedback['hi']['subtitle'],
            'icon': feedback['hi']['icon'],
        })
    else:
        title = feedback['med']['title'].format(goal=goal_title, num=completed)
        resp.update({
            'title': title,
            'subtitle': feedback['med']['subtitle'],
            'icon': feedback['med']['icon'],
        })

    # If wev'e
    if resp['incomplete'] == 0:
        resp['icon'] = 4
    return resp


def todays_customactions(user):
    """Return a queryset of CustomActions that are upcoming..."""
    today = local_day_range(user)  # start/end in UTC wrapping the user's day
    now = timezone.now()

    # Excluding those that have already been completed
    completed = user.usercompletedcustomaction_set.filter(
        updated_on__range=today,
        state=UserCompletedAction.COMPLETED
    )
    completed = completed.values_list('customaction', flat=True)
    upcoming_cas = user.customaction_set.filter(
        next_trigger_date__range=(now, today[1])
    )
    upcoming_cas = upcoming_cas.exclude(id__in=completed)
    upcoming_cas = upcoming_cas.order_by('next_trigger_date').distinct()
    return upcoming_cas


def todays_actions(user):
    """Return a QuerySet of UserAction objects that the user should perform
    today, ordered by `next_trigger_date` field (e.g. next up is first in the
    list).

    This result excludes any UserActions that have already been completed.

    """
    cache_key = TODAYS_ACTIONS.format(userid=user.id)
    results = cache.get(cache_key)
    if results is not None:
        return results

    # We want to show only those left for "today" (in the user's timezone)
    today = local_day_range(user)  # start/end in UTC wrapping the user's day
    now = timezone.now()

    # Exclude those that have been completed
    cids = user.usercompletedaction_set.filter(
        updated_on__range=today,
        state=UserCompletedAction.COMPLETED
    )
    cids = cids.values_list('useraction', flat=True)

    # The `next_trigger_date` should always be saved as UTC
    upcoming = user.useraction_set.select_related('action')
    upcoming = upcoming.filter(next_trigger_date__range=(now, today[1]))
    upcoming = upcoming.exclude(id__in=cids)
    upcoming = upcoming.order_by('next_trigger_date')

    # Now cache for a short time because other functions here use this.
    cache.set(cache_key, upcoming, timeout=TODAYS_ACTIONS_TIMEOUT)
    return upcoming


def todays_actions_progress(user):
    """Return some stats indicating to user's progress toward completing their
    actions that were scheduled for 'today'.

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

    --------------------------------------------------------------
    TODO: incorporate UserCompletedCustomAction data into this.
    --------------------------------------------------------------

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
    total = user.useraction_set.filter(
        Q(prev_trigger_date__range=today) |
        Q(next_trigger_date__range=today) |
        Q(id__in=useraction_ids)
    ).distinct().count()

    progress = 0
    if total > 0:
        progress = int(completed/total * 100)
    return {'completed': completed, 'total': total, 'progress': progress}


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
    # From the goals the user has _not_ selected (that are public)...
    user_selected_goals = user.usergoal_set.values_list("goal__id", flat=True)
    goals = Goal.objects.published()  # excludes goals in packaged content
    goals = goals.exclude(id__in=user_selected_goals)

    # -------------------------------------------------------------------------
    # TEMPORARY CHANGE? Forget the categories. Use the profile labels to choose
    # -------------------------------------------------------------------------
    # cats = user.usercategory_set.filter(category__state='published')
    # cats = cats.values_list('category', flat=True)

    # IF we've got sufficient number of categories, we can stick to the things
    # in the categories the user has chosen. If not, we'll just pull from
    # selected goals (otherwise there would be no suggestions)
    # category_goals = goals.filter(categories__in=cats)
    # if cats.count() and category_goals.count() > limit:
    #     goals = category_goals

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

        if profile.has_college_degree:
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

    # But we always want to use the male/female filter.
    if profile.sex == "Female":
        user_keywords.append('female')
    elif profile.sex == "Male":
        exclude_keywords.append('female')

    goals = goals.filter(keywords__overlap=user_keywords)
    goals = goals.exclude(keywords__overlap=exclude_keywords)

    # Pick a random sample of suggestions (or the leftover goals)...
    ids = list(goals.values_list("id", flat=True))
    if limit < len(ids):
        goals = Goal.objects.filter(id__in=random.sample(ids, limit))
    elif len(ids) > 0:
        goals = Goal.objects.filter(id__in=ids)
    else:
        # we filtered too much. Just pick some random things.
        goals = Goal.objects.published().exclude(id__in=user_selected_goals)
        goals = goals.exclude(keywords__contains=['sensitive']).distinct()
        goals = goals.values_list("id", flat=True)
        goals = Goal.objects.filter(id__in=random.sample(goals, limit))
    return goals[:limit]


def _usergoal_sorter(usergoal):
    return usergoal.progress_value


def selected_goals(user):
    """Return the user's selected goals, ... ideally sorted in order of
    upcoming events, but that's a nasty query :(

    For now: Sorted by progress value (low-to-high)
    """
    user_goals = user.usergoal_set.all()
    user_goals = sorted(user_goals, key=_usergoal_sorter)
    return [(ug.progress_value, ug) for ug in user_goals]
