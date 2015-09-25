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
from utils.user_utils import to_localtime
from .models import Goal, UserAction


def todays_actions(user):
    """return a list of actions that the user should perform today."""
    now = timezone.now()
    next_trigger_date = now + timedelta(days=1)
    user_actions = []

    for ua in user.useraction_set.all():
        if ua.custom_trigger:
            t = ua.custom_trigger.next()
        elif ua.default_trigger:
            t = ua.default_trigger.next()
        if t < next_trigger_date:
            user_actions.append(ua.id)

    return UserAction.objects.filter(id__in=user_actions)


def todays_actions_progress(useractions):
    """Return the status of completed or not for today's actions."""
    # e.g. you've completed X / Y activities for today.
    data = [1 if ua.completed_today else 0 for ua in useractions]
    completed = sum(data)
    total = len(data)
    progress = int(completed/total * 100)
    return {'completed': completed, 'total': total, 'progress': progress}


def next_user_action(user):
    """Looks at all of the user's selected Actions, generating the 'next'
    trigger time and returns the upcoming action."""

    if not user.is_authenticated():
        return None

    # TODO: instead of queyring this so inefficeintly, we could do this on save
    # for every UserAction, and store the value locally (resetting when it's
    # delivered?)
    #
    # That way we could query for this directly.

    now = timezone.now()
    next_trigger_date = now + timedelta(days=400)  # arbitrary far-off date
    next_ua = None

    for ua in user.useraction_set.all():
        t = None
        if ua.custom_trigger:
            t = ua.custom_trigger.next()
        elif ua.default_trigger:
            t = ua.default_trigger.next()

        if t is not None:
            t = to_localtime(t, user)
            if t > now and t < next_trigger_date:
                next_trigger_date = t
                next_ua = ua

    return next_ua


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
    # if profile.age
    # if profile.zipcode
    # if profile.gender ==

    # Pick a random sample of suggestions (or the leftover goals)...
    ids = list(goals.filter(criteria).values_list("id", flat=True))
    criteria = Q(id__in=random.sample(ids, limit))
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
