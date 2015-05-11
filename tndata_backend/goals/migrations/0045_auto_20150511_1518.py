# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import recurrence.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0044_auto_20150508_1628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='recurrences',
            field=recurrence.fields.RecurrenceField(null=True, help_text='An iCalendar (rfc2445) recurrence rule (an RRULE)'),
        ),
    ]
