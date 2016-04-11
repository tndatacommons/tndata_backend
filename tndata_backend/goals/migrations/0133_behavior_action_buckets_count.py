# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0132_update_point_of_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='behavior',
            name='action_buckets_count',
            field=jsonfield.fields.JSONField(blank=True, default=dict, help_text='A dictionary of counts for each action bucket'),
        ),
    ]
