# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


class TODSelector:
    """A dict-like object that returns a value for the Time of Day, given
    an hour.

    Usage:

        >>> tod = TODSelector()
        >>> tod[11]
        'noonish'

    """
    def __getitem__(self, key):
        if key is None:  # If no time is set, let's default to evening.
            return 'evening'

        # Otherwise, we hopefully got a time object.
        hour = key.hour

        if hour >= 6 and hour <= 8:
            return 'early'
        elif hour > 8 and hour <= 10:
            return 'morning'
        elif hour >= 11 and hour <= 13:
            return 'noonish'
        elif hour > 13 and hour <= 17:
            return 'afternoon'
        elif hour > 17 and hour <= 21:
            return 'evening'
        else:
            return 'late'


def convert_triggers_to_dynamic(apps, schema_editor):
    """Find all default triggers, set their dynamic fields, and remove the
    non-dynamic info.
    """
    tod = TODSelector()
    Trigger = apps.get_model("goals", "Trigger")
    for trigger in Trigger.objects.filter(user=None):
        # Set the dynamic fields
        trigger.frequency = 'multiweekly'
        trigger.time_of_day = tod[trigger.time]

        # Remove non-dynamic fields (keep stop on complete)
        trigger.time = None
        trigger.trigger_date = None
        trigger.recurrences = None
        trigger.start_when_selected = False
        trigger.disabled = False
        trigger.relative_value = 0
        trigger.relative_units = None
        trigger.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0129_auto_20160316_2025'),
    ]

    operations = [
        migrations.RunPython(convert_triggers_to_dynamic)
    ]
