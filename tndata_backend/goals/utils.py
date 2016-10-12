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

    Valid for Category, Goal, Action instances.

    """
    model = obj._meta.model_name
    if model not in ['category', 'goal', 'action']:
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


def delete_content(prefix):
    """Delete content whose title/name starts with the given prefix."""

    from goals.models import Action, Category, Goal, Trigger
    print("Deleting content that startswith='{}'".format(prefix))

    actions = Action.objects.filter(title__startswith=prefix)
    print("Deleting {} Actions...".format(actions.count()))
    actions.delete()

    triggers = Trigger.objects.filter(name__startswith=prefix)
    print("Deleting {} Triggers...".format(triggers.count()))
    triggers.delete()

    goals = Goal.objects.filter(title__startswith=prefix)
    print("Deleting {} Goals...".format(goals.count()))
    goals.delete()

    cats = Category.objects.filter(title__startswith=prefix)
    print("Deleting {} Categories...".format(cats.count()))
    cats.delete()

    print("...done.")
