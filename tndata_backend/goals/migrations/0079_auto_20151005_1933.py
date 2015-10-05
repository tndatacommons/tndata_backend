# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0078_goal_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='behaviorprogress',
            name='action_progress',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='behaviorprogress',
            name='actions_completed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='behaviorprogress',
            name='actions_total',
            field=models.IntegerField(default=0),
        ),
    ]
