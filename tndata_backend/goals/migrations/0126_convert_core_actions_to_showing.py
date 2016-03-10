# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def convert_core_to_showing(apps, schema_editor):
    Action = apps.get_model('goals', 'Action')
    Action.objects.filter(action_type='core').update(action_type='showing')


def convert_showing_to_core(apps, schema_editor):
    """Reverses `convert_core_to_showing`."""
    Action = apps.get_model('goals', 'Action')
    Action.objects.filter(action_type='showing').update(action_type='core')



class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0125_auto_20160309_2009'),
    ]

    operations = [
        migrations.RunPython(
            convert_core_to_showing,
            reverse_code=convert_showing_to_core
        )
    ]
