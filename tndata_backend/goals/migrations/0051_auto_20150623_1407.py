# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import recurrence.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0050_auto_20150610_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='trigger_date',
            field=models.DateField(blank=True, null=True, help_text='A date for a one-time trigger'),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='recurrences',
            field=recurrence.fields.RecurrenceField(blank=True, null=True, help_text='An iCalendar (rfc2445) recurrence rule (an RRULE)'),
        ),
    ]
