import csv
import re

from io import TextIOWrapper
from django.conf import settings


# Import clog if we're in debug otherwise make it a noop
if settings.DEBUG:
    from clog.clog import clog
else:
    def clog(*args, **kwargs):
        pass


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


def debug_user_data(user):
    """Given a user, print out their selected hierarchy of content."""

    data = {'orphaned': {'goals': [], 'actions': [], 'behaviors': []}}

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

    # Better representation.
    orphans = data.pop("orphaned")
    for cat, goals in data.items():
        print(cat)
        for goal, behaviors in goals.items():
            print("- {0}".format(goal))
            for behavior, actions in behaviors.items():
                print("-- {0}".format(behavior))
                for a in actions:
                    print("--- {0}".format(a))

    print("\nOrphaned data")
    for t, items in orphans.items():
        print("{0}: {1}".format(t, ", ".join(items)))
