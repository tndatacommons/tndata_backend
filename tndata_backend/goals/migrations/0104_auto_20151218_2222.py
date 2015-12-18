# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0103_useraction_serialized_primary_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='usergoal',
            name='serialized_goal',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='usergoal',
            name='serialized_goal_progress',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='usergoal',
            name='serialized_primary_category',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='usergoal',
            name='serialized_user_behaviors',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='usergoal',
            name='serialized_user_categories',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
    ]
