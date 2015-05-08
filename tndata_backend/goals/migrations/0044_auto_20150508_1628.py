# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0043_remove_trigger_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='trigger_type',
            field=models.CharField(max_length=10, choices=[('time', 'Time'), ('place', 'Place')], default='time', help_text='The type of Trigger used, e.g. a time-based trigger'),
        ),
    ]
