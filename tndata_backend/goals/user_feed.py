"""
TODO: WIP - A feed of relevant content for the user.

Our mobile app shows a feed of information to the user. This module compiles
that data, and exposes some utilities to construct that information.

Some possible data in the user's feed:

- Up Next: The Action that is up next for the user.
- Progress: Provide some sort of information regarding their progress toward
  selected goals (possibly related to the action that is _up next_).
- TEMPORARILY DISABLED Suggested Goals: If a user has no (or _few_) selected
  goals, give them a few suggestions based on their selected categories and/or
  demographics
- Selected Goals: All of the user's selected Goals.


See this trello card for more details:
https://trello.com/c/zKedLoZe/170-initial-home-feed

"""
import random

from collections import Counter
from datetime import timedelta
from django.core.cache import cache
from django.db.models import F, Q
from django.utils import timezone

from utils.dateutils import dates_range, weekday
from utils.user_utils import local_day_range

from .models import (
    CustomAction,
    DailyProgress,
    Goal,
    UserAction,
    UserCompletedAction,
    UserCompletedCustomAction,
    UserGoal,
)


# Some Cache keys.
TODAYS_ACTIONS = "todays_actions_{userid}"
TODAYS_ACTIONS_TIMEOUT = 30


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

    def _fill_streaks(input_values, days):
        """fills in data for missing dates"""
        dates = sorted([dt.date() for dt in dates_range(days)])
        index = 0  # index of the last, non-generated item
        for dt in dates:
            if index < len(input_values) and input_values[index][0] == dt:
                yield input_values[index]
                index += 1
            else:
                yield (dt, 0)

    # Generate streaks data & add actions/customactions completed
    progresses = DailyProgress.objects.filter(
        Q(actions_completed__gt=0) | Q(customactions_completed__gt=0), user=user
    ).annotate(
        total=F('actions_completed') + F('customactions_completed')
    ).distinct()
    progresses = progresses.values_list('updated_on', 'total')
    progresses = [(dt.date(), total) for dt, total in progresses]
    progresses = list(_fill_streaks(progresses, days=days))
    results = []
    for date, count in progresses:
        results.append({
            'date': date,
            'day': weekday(date),
            'count': count,
        })

    return results


def _useraction_feedback(useraction, dt):
    """Aggregate total, completed, and percetage values for the given
    UserAction on the given date (dt).

    Returns a dict of the form:

        {
            total: X,
            completed: X,
            percentage: X,
            incomplete: X,
            title: GOAL_TITLE,
        }

    """
    qs = useraction.usercompletedaction_set.filter(updated_on__gt=dt)
    total = qs.count()
    completed = qs.filter(state="completed").count()
    percentage = 0
    if total > 0:
        percentage = round((completed / total) * 100)

    goal_title = "achieve my goal"
    goal = useraction.get_primary_goal()
    if goal:
        goal_title = goal.title.lower()

    return {
        'total': total,
        'completed': completed,
        'percentage': percentage,
        'incomplete': total - completed,
        'title': goal_title,
    }


def _customaction_feedback(customaction, dt):
    """Aggregate total, completed, and percetage values for the given
    CustomAction on the given date (dt).

    Returns a dict of the form:

        {
            total: X,
            completed: X,
            percentage: X,
            incomplete: X,
            title: GOAL_TITLE,
        }

    """
    qs = customaction.usercompletedcustomaction_set.filter(updated_on__gte=dt)
    total = qs.count()
    completed = qs.filter(state="completed").count()
    percentage = 0
    if total > 0:
        percentage = round((completed / total) * 100)

    return {
        'total': total,
        'completed': completed,
        'percentage': percentage,
        'incomplete': total - completed,
        'title': customaction.customgoal.title or "my goal",
    }


def action_feedback(user, obj, lookback=30):
    """This function assembles data for *feedback* on the user's upcoming
    action or custom action. See: https://goo.gl/7UUjzq

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
    * obj - the user's next action (a UserAction or CustomAction instance)
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
            'title': "You've done some work to {goal} this month!",
            'subtitle': 'Even small steps can help you reach your goal',
            'icon': 1,
        },
        'med': {
            'title': "You've done {num} activities to {goal} this month!",
            'subtitle': 'You must really want this!',
            'icon': 2,
        },
        'hi': {
            'title': (
                "You've done {num} out of {total} activities to {goal} "
                "this month!"
            ),
            'subtitle': "You're doing great! Schedule another activity!",
            'icon': 3,
        },
    }
    # Data points needed:
    # - total number of UserActions for the time period
    # - completed UserActions for the time period.
    # - percentage of Actions completed/scheduled in some period (lookback)
    # - icons indicate which icon in the app should be displayed:
    #   1: footsteps, 2: thumbs-up, 3: ribbon, 4: trophy (when all are completed)

    # NOTE: UserActions always get updated with the *next up* trigger date
    # so we can't use them to calculate the above. For now, we'll just use
    # the UserCompletedAction model, but that will only work if the user has the
    # version of the app that records incomplete as well as completed actions.
    resp = {
        'title': '',
        'subtitle': '',
        'total': 0,
        'completed': 0,
        'incomplete': 0,
        'percentage': 0,
        'icon': 1,
    }
    dt = timezone.now() - timedelta(days=lookback)
    if isinstance(obj, UserAction):
        resp.update(_useraction_feedback(obj, dt))
    elif isinstance(obj, CustomAction):
        resp.update(_customaction_feedback(obj, dt))

    if resp['percentage'] <= 20:
        title = feedback['low']['title'].format(goal=resp['title'])
        resp.update({
            'title': title,
            'subtitle': feedback['low']['subtitle'],
            'icon': feedback['low']['icon'],
        })
    elif resp['percentage'] >= 60:
        title = feedback['hi']['title'].format(
            goal=resp['title'], num=resp['completed'], total=resp['total']
        )
        resp.update({
            'title': title,
            'subtitle': feedback['hi']['subtitle'],
            'icon': feedback['hi']['icon'],
        })
    else:
        title = feedback['med']['title'].format(
            goal=resp['title'], num=resp['completed']
        )
        resp.update({
            'title': title,
            'subtitle': feedback['med']['subtitle'],
            'icon': feedback['med']['icon'],
        })

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
    """A combination of todays progress on Actions + Custom Actions.  This
    combines the results of the following:

    * todays_actions_progress
    * todays_customactions_progress

    """
    results = todays_actions_progress(user)
    custom = todays_customactions_progress(user)

    # Add the values together using a counter
    results = Counter(results)
    results.update(custom)
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
