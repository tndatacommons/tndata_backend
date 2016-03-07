# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def convert_custom_to_core(apps, schema_editor):
    Action = apps.get_model('goals', 'Action')
    Action.objects.filter(action_type='custom').update(action_type='core')


def convert_core_to_custom(apps, schema_editor):
    """Reverses `convert_custom_to_core`."""
    Action = apps.get_model('goals', 'Action')
    Action.objects.filter(action_type='core').update(action_type='custom')


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0121_action_priority'),
    ]

    operations = [
        migrations.RunPython(
            convert_custom_to_core,
            reverse_code=convert_core_to_custom
        )
    ]
