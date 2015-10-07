# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0082_fill_goalprogress_usergoal'),
    ]

    operations = [
        migrations.RenameField(
            model_name='behaviorprogress',
            old_name='action_progress',
            new_name='daily_action_progress',
        ),
        migrations.RenameField(
            model_name='behaviorprogress',
            old_name='actions_completed',
            new_name='daily_actions_completed',
        ),
        migrations.RenameField(
            model_name='behaviorprogress',
            old_name='actions_total',
            new_name='daily_actions_total',
        ),
    ]
