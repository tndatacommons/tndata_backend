import csv
from io import TextIOWrapper
from django.conf import settings


# Import clog if we're in debug otherwise make it a noop
if settings.DEBUG:
    from clog import clog
else:
    def clog(*args, **kwargs):
        pass


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
