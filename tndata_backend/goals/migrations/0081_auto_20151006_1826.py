# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0080_auto_20151005_2220'),
    ]

    operations = [
        migrations.AddField(
            model_name='goalprogress',
            name='action_progress',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='actions_completed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='actions_total',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='daily_action_progress',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='daily_actions_completed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='daily_actions_total',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='usergoal',
            field=models.ForeignKey(null=True, to='goals.UserGoal'),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='weekly_action_progress',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='weekly_actions_completed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='weekly_actions_total',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name='goalprogress',
            unique_together=set([('user', 'goal', 'reported_on')]),
        ),
    ]
