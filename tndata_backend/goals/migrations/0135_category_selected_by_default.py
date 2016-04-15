# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0134_count_behavior_actions'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='selected_by_default',
            field=models.BooleanField(default=False, help_text='Should this category and all of its content be auto-selected for new users?'),
        ),
    ]
