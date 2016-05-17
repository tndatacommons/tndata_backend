# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0143_auto_20160509_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='time_of_day',
            field=models.CharField(null=True, help_text='Select a time of day, and a notification will be sent at some point during that time.', blank=True, choices=[('early', 'Early Morning'), ('morning', 'Mid-Late Morning'), ('noonish', 'Around Noon'), ('afternoon', 'Afternoon'), ('evening', 'Evening'), ('late', 'During the night'), ('allday', 'During the day')], max_length=32),
        ),
    ]
