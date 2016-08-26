"""
Tools/utils/playground for Goal/Behavior/Action sequences

"""
from collections import defaultdict
from goals.models import Goal, Category
from goals.models import UserCompletedAction


def get_next_useractions_in_sequence(user, goal=None, category=None):
    """Return a queryset of UserActions that are due for delivery based on
    the sequeunce of Goals, Behaviors, Actions, and whether or not a user
    has completed the Action, the entire Behavior, and/or the Goal.

    """
    # Goals that are 'up next' (lowest sequence number this is not completed)
    if category:
        goals = user.usergoal_set.next_in_sequence(
            published=True, goal__categories=category)
    elif goal:
        goals = user.usergoal_set.next_in_sequence(published=True, goal=goal)
    else:
        goals = user.usergoal_set.next_in_sequence(published=True)
    goals = goals.values_list('goal', flat=True)

    # Uncompleted behaviors within those goals.
    behaviors = user.userbehavior_set.next_in_sequence(
        published=True,
        goals=goals
    )
    behaviors = behaviors.values_list("behavior", flat=True)

    # Return the related UserAction objects.
    return user.useraction_set.next_in_sequence(behaviors, published=True)


# --- the following are just debugging tools ------------


def get_next_in_sequence_data(user, print_them=True):
    goals = []
    behaviors = []
    behavior_ids = []
    actions = []

    # Nested data containing
    #   {
    #       Goal: {
    #           Behavior:  [
    #               Actions, ... ]
    #           }
    #       }
    #   }
    data = {}

    for ug in user.usergoal_set.next_in_sequence():
        entry = "{}) {}".format(ug.goal.order, ug.goal.title)
        goals.append(entry)
        data[entry] = defaultdict(dict)

    for ub in user.userbehavior_set.next_in_sequence():
        entry = "{}) {}".format(ub.behavior.order, ub.behavior.title)
        behaviors.append(entry)
        behavior_ids.append(ub.behavior.id)
        for goal in ub.behavior.goals.all():
            goal = "{}) {}".format(goal.order, goal.title)
            if goal in data:
                data[goal][entry] = []

    for ua in user.useraction_set.next_in_sequence(behaviors=behavior_ids):
        entry = "{}) {}".format(ua.action.order, ua.action.title)
        actions.append(entry)

        for goal in ua.action.behavior.goals.all():
            goal = "{}) {}".format(goal.order, goal.title)
            behavior = "{}) {}".format(ua.action.behavior.order, ua.action.behavior.title)
            if goal in data and behavior in data[goal]:
                data[goal][behavior].append(entry)

    if print_them:
        from clog.clog import clog
        print("\n\nGOALS\n{}".format("\n".join(goals)))
        print("\nBEHAVIORS\n{}".format("\n".join(behaviors)))
        print("\nACTIONS\n{}".format("\n".join(actions)))
        clog(data, title="nested data")
    else:
        return data

def complete_behavior(user, userbehavior):
    # GIVEN a behavior, set ALL of it's actions to compelted, and set it compelted
    for ua in user.useraction_set.filter(action__behavior=userbehavior.behavior):
        _complete_useraction(ua)
    userbehavior.completed = True
    userbehavior.save()


def complete_action(user, seq):
    # GIVEN A sequence_order number (seq), create a UserCompletedAction obj
    # fo the give user, for all actions matching that number
    for ua in user.useraction_set.filter(action__sequence_order=seq):
        _complete_useraction(ua)


def _complete_useraction(useraction):
    ua = useraction
    user = useraction.user
    action = useraction.action

    try:
        uca = UserCompletedAction.objects.filter(user=user, useraction=ua).latest()
        uca.state = UserCompletedAction.COMPLETED
        uca.save()
    except UserCompletedAction.DoesNotExist:
        UserCompletedAction.objects.create(
            user=user,
            useraction=ua,
            action=action,
            state=UserCompletedAction.COMPLETED
        )


def set_sequence_orders(category_title='Teen Nurturing Parenting'):
    # assign sequence_orders to all the items in Teen Nuturing Parenting
    cat = Category.objects.get(title=category_title)
    goals = Goal.objects.filter(categories=cat)

    gslots = int(goals.count() / 3)
    gslot = 0
    gcount = 0
    for goal in goals:
        goal.sequence_order = gslot
        goal.save()
        gcount += 1
        if gcount >= gslots:
            gcount = 0
            gslot += 1

        bslots = int(goal.behavior_set.all().count() / 4)
        bslot = 0
        bcount = 0
        for b in goal.behavior_set.all():
            b.sequence_order = bslot
            b.save()
            bcount += 1
            if bcount >= bslots:
                bcount = 0
                bslot += 1

            aslots = int(b.action_set.all().count() / 8)
            aslot = 0
            acount = 0
            for a in b.action_set.all():
                a.sequence_order = aslot
                a.save()
                acount += 1
                if acount >= aslots:
                    acount = 0
                    aslot += 1
