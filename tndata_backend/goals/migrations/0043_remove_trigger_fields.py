# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0042_trigger_recurrences'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trigger',
            name='date',
        ),
        migrations.RemoveField(
            model_name='trigger',
            name='frequency',
        ),
        migrations.RemoveField(
            model_name='trigger',
            name='instruction',
        ),
        migrations.RemoveField(
            model_name='trigger',
            name='text',
        ),
        migrations.AlterField(
            model_name='trigger',
            name='trigger_type',
            field=models.CharField(help_text='The type of Trigger used, e.g. a time-based trigger', max_length=10, default='time', choices=[('time', 'Time')]),
        ),
    ]
