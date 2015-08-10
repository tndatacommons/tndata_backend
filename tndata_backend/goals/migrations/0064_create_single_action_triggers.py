# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.text import slugify


def create_single_default_trigger_for_actions(apps, schema_editor):
    Action = apps.get_model("goals", "Action")
    Trigger = apps.get_model("goals", "Trigger")
    for action in Action.objects.filter(default_trigger__isnull=False):
        # Create a new, duplicate trigger
        trigger_name = "Default for {0}-{1}".format(action, action.id)
        try:
            # Ensure this doesn't already exist.
            Trigger.objects.get(name=trigger_name)
            trigger_name = "New {0}".format(trigger_name)
        except Trigger.DoesNotExist:
            pass  # We're OK

        t = Trigger.objects.create(
            name=trigger_name,
            name_slug=slugify(trigger_name),
            trigger_type=action.default_trigger.trigger_type,
            location=action.default_trigger.location,
            time=action.default_trigger.time,
            trigger_date=action.default_trigger.trigger_date,
            recurrences=action.default_trigger.recurrences,
        )
        action.new_default_trigger = t
        action.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0063_action_new_default_trigger'),
    ]

    operations = [
        migrations.RunPython(create_single_default_trigger_for_actions),
    ]
