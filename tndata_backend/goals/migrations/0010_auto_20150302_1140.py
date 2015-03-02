# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0009_goal_icon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='behaviorsequence',
            name='interests',
        ),
        migrations.RemoveField(
            model_name='goal',
            name='interests',
        ),
    ]
