# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models

import re

# This migration will inspect title/notification fields in goal models that
# containing content written in the first person, e.g. I and change it to the
# second person.
#
#     I --> you
#     me --> you
#     myself --> yourself
#     my --> your
#     mine --> your
#     we --> you
#     us --> you
#     ourselves --> yourselves
#     our --> your
#     ours --> yours
#     am --> are


def update_text(text):
    """A function to swap out the words we want to change"""

    if not text:  # Leave empty content as-is
        return text

    # Words we want to change.
    changes = {
        'I': 'you',
        'me': 'you',
        'myself': 'yourself',
        'my': 'your',
        'mine': 'your',
        'we': 'you',
        'us': 'you',
        'ourselves': 'yourselves',
        'our': 'your',
        'ours': 'yours',
        'am': 'are',
    }

    for old_word, new_word in changes.items():
        results = []
        for word in text.split():
            # \b Matches the empty string, but only at the beginning
            #    or end of a word.
            pattern = r"\b{}\b".format(old_word)
            word = re.sub(pattern, new_word, word)
            results.append(word)
        text = " ".join(results)
    return text


def change_person(apps, schema_editor):
    Action = apps.get_model("goals", "Action")
    Behavior = apps.get_model("goals", "Behavior")
    Goal = apps.get_model("goals", "Goal")

    for action in Action.objects.all():
        action.title = update_text(action.title)
        action.notification_text = update_text(action.notification_text)
        action.save()

    for behavior in Behavior.objects.all():
        behavior.title = update_text(behavior.title)
        behavior.save()

    for goal in Goal.objects.all():
        goal.title = update_text(goal.title)
        goal.subtitle = update_text(goal.subtitle)
        goal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0131_update_action_notification_text'),
    ]

    operations = [
        migrations.RunPython(change_person)
    ]
