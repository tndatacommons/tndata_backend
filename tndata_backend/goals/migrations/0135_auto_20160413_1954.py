# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0134_count_behavior_actions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='goal',
            options={'verbose_name': 'Goal', 'verbose_name_plural': 'Goals', 'permissions': (('view_goal', 'Can view Goals'), ('decline_goal', 'Can Decline Goals'), ('publish_goal', 'Can Publish Goals')), 'ordering': ['sequence_order', 'title']},
        ),
        migrations.AddField(
            model_name='goal',
            name='sequence_order',
            field=models.IntegerField(db_index=True, default=0, blank=True, help_text='Optional ordering for a sequence of goals'),
        ),
    ]
