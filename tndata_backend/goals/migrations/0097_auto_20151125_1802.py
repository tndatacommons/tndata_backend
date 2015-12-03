# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0096_trigger_stop_on_complete'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='relative_units',
            field=models.CharField(blank=True, null=True, choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=32),
        ),
        migrations.AddField(
            model_name='trigger',
            name='relative_value',
            field=models.IntegerField(default=0),
        ),
    ]
