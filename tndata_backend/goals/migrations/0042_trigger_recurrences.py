# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import recurrence.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0041_auto_20150504_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='recurrences',
            field=recurrence.fields.RecurrenceField(null=True),
        ),
    ]
