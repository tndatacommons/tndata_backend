"""
Tools/utils/playground for Goal/Behavior/Action sequences

"""
from django.contrib.auth import get_user_model
from goals.models import Goal, Category
from goals.models import UserAction, UserBehavior, UserGoal, UserCompletedAction


def get_next_useractions_in_sequence(user):
    """Return a queryset of UserActions that are due for delivery based on
    the sequeunce of Goals, Behaviors, Actions, and whether or not a user
    has completed the Action, the entire Behavior, and/or the Goal.

    """
    # Goals that are 'up next' (lowest sequence number this is not completed)
    goals = user.usergoal_set.next_in_sequence(published=True)
    goals = goals.values_list('goal', flat=True)

    # Uncompleted behaviors within those goals.
    behaviors = user.userbehavior_set.next_in_sequence(published=True)
    behaviors = behaviors.filter(behavior__goals__in=goals)
    behaviors = behaviors.values_list("behavior", flat=True)

    # Return the related UserAction objects.
    return user.useraction_set.next_in_sequence(behaviors, published=True)

# --- the following are just debugging tools ------------


def print_next(user):
    User = get_user_model()
    user = User.objects.get(username='bkmontgomery')

    goals = []
    behaviors = []
    actions = []

    ugs = UserGoal.objects.next_in_sequence(user=user)
    for ug in ugs:
        goals.append("{} - {}".format(ug.goal.sequence_order, ug.goal.title))
        print("{}] {}".format(ug.goal.sequence_order, ug.goal))
        ubs = UserBehavior.objects.next_in_sequence(user=user, behavior__goals=ug.goal)
        for ub in ubs:
            behaviors.append("{} - {}".format(ub.behavior.sequence_order, ub.behavior.title))
            print("- {}] {}".format(ub.behavior.sequence_order, ub.behavior))
            uas = UserAction.objects.next_in_sequence(ub.behavior, user=user)
            for ua in uas.order_by('action'):
                actions.append("{} - {}".format(ua.action.sequence_order, ua.action.title))
                print("-- {}] {}".format(ua.action.sequence_order, ua.action))

    print("\n\nGOALS\n{}".format("\n".join(goals)))
    print("\nBEHAVIORS\n{}".format("\n".join(behaviors)))
    print("\nACTIONS\n{}".format("\n".join(actions)))


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
