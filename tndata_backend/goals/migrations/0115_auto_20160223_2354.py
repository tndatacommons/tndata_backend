# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0114_auto_20160222_1530'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='behaviorprogress',
            name='user',
        ),
        migrations.RemoveField(
            model_name='behaviorprogress',
            name='user_behavior',
        ),
        migrations.RemoveField(
            model_name='categoryprogress',
            name='category',
        ),
        migrations.RemoveField(
            model_name='categoryprogress',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='goalprogress',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='goalprogress',
            name='goal',
        ),
        migrations.RemoveField(
            model_name='goalprogress',
            name='user',
        ),
        migrations.RemoveField(
            model_name='goalprogress',
            name='usergoal',
        ),
        migrations.DeleteModel(
            name='BehaviorProgress',
        ),
        migrations.DeleteModel(
            name='CategoryProgress',
        ),
        migrations.DeleteModel(
            name='GoalProgress',
        ),
    ]
