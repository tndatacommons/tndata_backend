# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0090_auto_20151102_2047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraction',
            name='next_trigger_date',
            field=models.DateTimeField(help_text='The next date/time that a notification for this action will be triggered (this is auto-populated and is in UTC).', blank=True, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='useraction',
            name='prev_trigger_date',
            field=models.DateTimeField(help_text='The previous date/time that a notification for this action was be triggered (this is auto-populated and is in UTC).', blank=True, null=True, editable=False),
        ),
    ]
