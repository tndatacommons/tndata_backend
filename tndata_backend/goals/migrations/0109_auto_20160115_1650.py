# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0108_auto_20160104_2118'),
    ]

    operations = [
        migrations.AddField(
            model_name='behavior',
            name='actions_count',
            field=models.IntegerField(default=0, blank=True, help_text='The number of (published) child actions in this Behavior'),
        ),
        migrations.AddField(
            model_name='behavior',
            name='goal_ids',
            field=django.contrib.postgres.fields.ArrayField(default=list, blank=True, help_text='Pre-rendered list of parent goal IDs', base_field=models.IntegerField(blank=True), size=None),
        ),
        migrations.AddField(
            model_name='goal',
            name='behaviors_count',
            field=models.IntegerField(default=0, blank=True, help_text='The number of (published) child Behaviors in this Goal'),
        ),
        migrations.AddField(
            model_name='goal',
            name='category_ids',
            field=django.contrib.postgres.fields.ArrayField(default=list, blank=True, help_text='Pre-rendered list of parent category IDs', base_field=models.IntegerField(blank=True), size=None),
        ),
    ]
