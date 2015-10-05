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
from django.db.models import Q
from django.utils import timezone
from .models import Goal, UserAction, UserCompletedAction


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
            'percentage': <percentage: completed / total>
        }

    """
    feedback = {
        'low': {
            'title': "I've done some work to {goal} this month!",
            'subtitle': 'Every action taken brings me closer',
        },
        'med': {
            'title': "I've done {num} activities to {goal} this month!",
            'subtitle': 'I must really want this!',
        },
        'hi': {
            'title': (
                "I've done {num} out of {total} activities to {goal} "
                "this month!"
            ),
            'subtitle': "I'm doing great! I'll schedule another activity!",
        },
    }
    # Data points needed:
    # - total number of UserActions for the time period
    # - completed UserActions for the time period.
    # - percentage of Actions completed/scheduled in some period (lookback)

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
    }

    if percentage <= 20:
        title = feedback['low']['title'].format(goal=goal_title)
        resp.update({
            'title': title,
            'subtitle': feedback['low']['subtitle']
        })
    elif percentage >= 60:
        title = feedback['hi']['title'].format(
            goal=goal_title, num=completed, total=total
        )
        resp.update({
            'title': title,
            'subtitle': feedback['hi']['subtitle']
        })
    else:
        title = feedback['med']['title'].format(goal=goal_title, num=completed)
        resp.update({
            'title': title,
            'subtitle': feedback['med']['subtitle']
        })
    return resp


def todays_actions(user):
    """return a list of actions that the user should perform today."""
    now = timezone.now()
    upcoming = UserAction.objects.upcoming().filter(user=user)
    upcoming = upcoming.filter(
        next_trigger_date__year=now.year,
        next_trigger_date__month=now.month,
        next_trigger_date__day=now.day,
    )
    return upcoming.order_by('next_trigger_date')


def todays_actions_progress(useractions):
    """Return the status of completed or not for today's actions."""
    # e.g. you've completed X / Y activities for today.
    data = [1 if ua.completed_today else 0 for ua in useractions]
    completed = sum(data)
    total = len(data)
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

    At the moment, it:

    - checks if you're in a relationship
    - if you're a parent

    and filters on Goal title's based on those 2 criteria, then picks 5 items
    at random.

    If you don' match any of those, you get served random goals.

    """
    # From the goals the user has _not_ selected (that are public)...
    user_selected_goals = user.usergoal_set.values_list("goal__id", flat=True)
    goals = Goal.objects.published().exclude(
        categories__packaged_content=True,
        id__in=user_selected_goals
    )

    # Use some details from the user's profile to filter these...
    criteria = Q()

    profile = user.userprofile
    if profile.has_relationship:
        rels = (
            Q(title__icontains='relationship') |
            Q(description__icontains='relationship') |
            Q(title__icontains='family') |
            Q(description__icontains='family') |
            Q(title__icontains='partner') |
            Q(description__icontains='parner')
        )
        criteria = criteria.add(rels, Q.OR)

    if profile.is_parent:
        rels = (
            Q(title__icontains='child') |
            Q(title__icontains='parent') |
            Q(description__icontains='parent')
        )
        criteria = criteria.add(rels, Q.OR)

    # TODO: what should we do for the following attributes?
    # NOTE: we're going to change onboarding to get binary results for
    # questions, and with the Goal's keywords, we can do a better job of
    # matching things up.
    #
    # if profile.age
    # if profile.zipcode
    # if profile.gender

    # Pick a random sample of suggestions (or the leftover goals)...
    ids = list(goals.filter(criteria).values_list("id", flat=True))
    if limit < len(ids):
        criteria = Q(id__in=random.sample(ids, limit))
    else:
        criteria = Q(id__in=ids)
    return goals.filter(criteria)[:limit]


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
