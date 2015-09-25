# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0075_usercompletedaction_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='next_trigger_date',
            field=models.DateTimeField(blank=True, null=True, help_text='The next date/time that a notification for this action will be triggered (this is auto-populated).'),
        ),
    ]
