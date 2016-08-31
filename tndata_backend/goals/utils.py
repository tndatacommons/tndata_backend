import csv
import re

from io import TextIOWrapper
from django.conf import settings
from django.core.cache import cache
from django.utils.termcolors import colorize

# Import clog if we're in debug otherwise make it a noop
if settings.DEBUG:
    from clog.clog import clog
else:
    def clog(*args, **kwargs):
        pass


def pop_first(data, key):
    """Pop the given key from the given `data` dict, and if the popped item
    is a list, return the first element.  This is handy for those cases where,
    in the api, `request.data.pop(whatever)` sometimes gives a list and other
    times is an object.

    """
    result = data.pop(key)
    if isinstance(result, list):
        result = result[0]
    return result


def num_user_selections(obj):
    """Return a count of the given object's UserXXXX instances (where XXXX is
    the name of one of our content models). This will tell how many users
    have selected this item.

    Valid for Category, Goal, Behavior, Action instances.

    """
    model = obj._meta.model_name
    if model not in ['category', 'goal', 'behavior', 'action']:
        raise ValueError("{0} is not a supported object type".format(model))
    method = "user{0}_set".format(model)
    return getattr(obj, method).count()


# ------------------------------------------
#
# Helper functions for cleaning text content
#
# ------------------------------------------
def clean_title(text):
    """Titles: collapse all whitespace, remove ending periods, strip."""
    if text:
        text = re.sub(r'\s+', ' ', text).strip()  # collapse whitespace
        if text.endswith("."):
            text = text[:-1]
    return text


def clean_notification(text):
    """Notification text: collapse all whitespace, strip, include an ending
    period (if not a ? or a !).
    """
    if text:
        text = re.sub(r'\s+', ' ', text).strip()  # collapse whitespace
        if text[-1] not in ['.', '?', '!']:
            text += "."
    return text


def strip(text):
    """Conditially call text.strip() if the input text is truthy."""
    if text:
        text = text.strip()
    return text


def read_uploaded_csv(uploaded_file, encoding='utf-8', errors='ignore'):
    """This is a generator that takes an uploaded file (such as an instance of
    InMemoryUploadedFile.file), converts it to a string (instead of bytes)
    representation, then parses it as a CSV.

    Returns a list of lists containing strings, and removes any empty rows.

    NOTES:

    1. This makes a big assumption about utf-8 encodings, and the errors
       param means we potentially lose data!
    2. InMemoryUploadedFileSee: http://stackoverflow.com/a/16243182/182778

    """
    file = TextIOWrapper(
        uploaded_file.file,
        encoding=encoding,
        newline='',
        errors=errors
    )
    for row in csv.reader(file):
        if any(row):
            yield row


def debug_user_data(user, **kwargs):
    """Given a user, print out their selected hierarchy of content.

    Available keywords:

    * only_categories: Print only the user's selected categories.
    * only_goals: Print only the user's selected goals.
    * only_behaviors: Print only the user's selected behaviors.
    * only_actions: Print only the user's selected actions.

    The above options are mutually exclusive.

    """

    data = {'orphaned': {'goals': [], 'actions': [], 'behaviors': []}}

    only_categories = kwargs.pop('only_categories', False)
    only_goals = kwargs.pop('only_goals', False)
    only_behaviors = kwargs.pop('only_behaviors', False)
    only_actions = kwargs.pop('only_actions', False)

    for uc in user.usercategory_set.all():
        data[uc.category.title] = {}

    for ug in user.usergoal_set.all():
        added = False
        for cat in ug.goal.categories.all():
            try:
                data[cat.title][ug.goal.title] = {}
                added = True
            except KeyError:
                pass

        if not added:
            data['orphaned']['goals'].append(ug.goal.title)

    for ub in user.userbehavior_set.all():
        added = False
        for goal in ub.behavior.goals.all():
            for cat in goal.categories.all():
                try:
                    data[cat.title][goal.title][ub.behavior.title] = []
                    added = True
                except KeyError:
                    pass
        if not added:
            data['orphaned']['behaviors'].append(ug.behavior.title)

    for ua in user.useraction_set.all():
        behavior = ua.action.behavior
        action = ua.action
        added = False
        for goal in behavior.goals.all():
            for cat in goal.categories.all():
                try:
                    data[cat.title][goal.title][behavior.title].append(action.title)
                    added = True
                except KeyError:
                    pass

        if not added:
            data['orphaned']['actions'].append(action.title)

    # List cached info
    key = 'userviewset-{}'.format(user.id)
    cached_data = cache.get(key)
    if cached_data is not None:
        print("Cached data for /api/users/")
        print("---------------------------")
        items = [d['category']['title'] for d in cached_data[0].get('categories')]
        print("Categories: {}".format(", ".join(items)))
        items = [d['goal']['title'] for d in cached_data[0].get('goals')]
        print("Goals: {}".format(", ".join(items)))
        items = [d['behavior']['title'] for d in cached_data[0].get('behaviors')]
        print("Behaviors: {}".format(", ".join(items)))
        items = [d['action']['title'] for d in cached_data[0].get('actions')]
        print("Actions: {}".format(", ".join(items)))
        print("---------------------------")

    # Better representation.
    orphans = data.pop("orphaned")
    print("\nSelected content:")
    for cat, goals in data.items():
        if not any([only_goals, only_behaviors, only_actions]):
            print(colorize("\n" + cat, fg="yellow"))
        for goal, behaviors in goals.items():
            if not any([only_categories, only_behaviors, only_actions]):
                print("- {0}".format(goal))
            for behavior, actions in behaviors.items():
                if not any([only_categories, only_goals, only_actions]):
                    print("-- {0}".format(behavior))
                for a in actions:
                    if not any([only_categories, only_goals, only_behaviors]):
                        print("--- {0}".format(a))

    if not any([only_categories, only_goals, only_behaviors, only_actions]):
        print("\nOrphaned data")
        for t, items in orphans.items():
            print("{0}: {1}".format(t, ", ".join(items)))


def delete_content(prefix):
    """Delete content whose title/name starts with the given prefix."""

    from goals.models import Action, Behavior, Category, Goal, Trigger
    print("Deleting content that startswith='{}'".format(prefix))

    actions = Action.objects.filter(title__startswith=prefix)
    print("Deleting {} Actions...".format(actions.count()))
    actions.delete()

    triggers = Trigger.objects.filter(name__startswith=prefix)
    print("Deleting {} Triggers...".format(triggers.count()))
    triggers.delete()

    behaviors = Behavior.objects.filter(title__startswith=prefix)
    print("Deleting {} Behaviors...".format(behaviors.count()))
    behaviors.delete()

    goals = Goal.objects.filter(title__startswith=prefix)
    print("Deleting {} Goals...".format(goals.count()))
    goals.delete()

    cats = Category.objects.filter(title__startswith=prefix)
    print("Deleting {} Categories...".format(cats.count()))
    cats.delete()

    print("...done.")


def delete_boilerplate_actions(boilerplate_category, categories_to_delete):
    """Delete the Actions whose titles match those in the given
    `boilerplate_category`. This is a way for us to "undo" our copying of
    actions into multiple categories (see the `duplicate_actions_into_behaviors`
    management command).

    * boilerplate_category - The PK for the Category from which actions were
      copied.
    * categories_to_delete - A list of category PK's from which these actions
      will be removed.

    -----

    USAGE: delete_boilerplate_actions(48, [18, 35, 36, 44])

    """
    from goals.models import Category, Action, UserAction

    total = 0
    total_cats = 0
    slugs = []

    try:
        cat = Category.objects.get(id=boilerplate_category)
        actions = Action.objects.filter(behavior__goals__categories=cat).distinct()
        slugs = list(actions.values_list('title_slug', flat=True))
    except Category.DoesNotExist:
        err = "Couldn't find the Boilerplate category: {}"
        print(err.format(boilerplate_category))
        return False

    for cat_id in categories_to_delete:
        try:
            cat = Category.objects.get(pk=cat_id)
            actions = Action.objects.filter(
                behavior__goals__categories=cat,
                title_slug__in=slugs
            ).distinct()
            print("\nFound {} actions in '{}' (pk={})\n".format(
                actions.count(), cat, cat_id))
            for action in actions:
                action_id = action.id
                print("{}) {}".format(action_id, action))
                print("--> has {} useractions".format(action.useraction_set.count()))
                action.delete()
                print("--> {} UserAction's remain".format(
                    UserAction.objects.filter(action__id=action_id).count()))
                print("-----------------------------")
                total += 1
            total_cats += 1
        except Category.DoesNotExist:
            print("Skipping Category: {}".format(cat_id))

    print("Removed {} total Actions from {} categories".format(total, total_cats))
