# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0076_useraction_next_trigger_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='primary_goal',
            field=models.ForeignKey(help_text='A primary goal associated with this action. Typically this is the goal through which a user navigated to find the action.', blank=True, to='goals.Goal', null=True),
        ),
        migrations.AlterField(
            model_name='useraction',
            name='next_trigger_date',
            field=models.DateTimeField(help_text='The next date/time that a notification for this action will be triggered (this is auto-populated and is in UTC).', blank=True, null=True),
        ),
    ]
