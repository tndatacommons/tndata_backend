# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0145_action_external_resource_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyprogress',
            name='checkin_streak',
            field=models.IntegerField(default=0, blank=True, help_text='A count of check-in streaks (how many days in a row a user has submitted a daily check-in.'),
        ),
    ]
