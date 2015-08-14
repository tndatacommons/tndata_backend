# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0067_auto_20150810_2147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='trigger_date',
            field=models.DateField(blank=True, null=True, help_text='A starting date for a recurrence, or a single date for a one-time trigger.'),
        ),
    ]
