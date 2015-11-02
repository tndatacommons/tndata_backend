# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def remove_place_triggers(apps, schema_editor):
    """Remove all Trigger.trigger_type = 'place' instances."""
    Trigger = apps.get_model('goals', 'Trigger')
    for t in Trigger.objects.filter(trigger_type='place'):
        t.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0086_auto_20151026_2059'),
    ]

    operations = [
        migrations.RunPython(remove_place_triggers),
    ]
