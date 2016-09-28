"""
Tools/utils/playground for Goal/Action sequences

"""
from collections import defaultdict
from goals.models import UserCompletedAction


def get_next_useractions_in_sequence(user, goal=None, category=None):
    """Return a queryset of UserActions that are due for delivery based on
    the sequeunce of Goals, Behaviors, Actions, and whether or not a user
    has completed the Action, the entire Behavior, and/or the Goal.

    """
    # Goals that are 'up next' (lowest sequence number that is not completed)
    if category:
        goals = user.usergoal_set.next_in_sequence(
            published=True, goal__categories=category)
    elif goal:
        goals = user.usergoal_set.next_in_sequence(published=True, goal=goal)
    else:
        goals = user.usergoal_set.next_in_sequence(published=True)
    goals = goals.values_list('goal', flat=True)

    # Return the related UserAction objects.
    return user.useraction_set.next_in_sequence(goals=goals, published=True)
