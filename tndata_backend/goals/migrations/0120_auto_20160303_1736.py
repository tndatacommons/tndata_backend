# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0119_auto_20160302_2314'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='frequency',
            field=models.CharField(help_text='Select a frequency to determine how often a reminder should be sent.', null=True, choices=[('daily', 'Daily'), ('weekends', 'During the weekend'), ('biweekly', 'A couple times a week'), ('weekly', 'Once a week'), ('monthly', 'Once a month')], blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='trigger',
            name='time_of_day',
            field=models.CharField(help_text='Select a time of day, and a notification will be sent at some point during that time.', null=True, choices=[('early', 'Early Morning'), ('morning', 'Mid-Late Morning'), ('noonish', 'Around Noon'), ('afternoon', 'Afternoon'), ('evening', 'Evening'), ('late', 'During the night')], blank=True, max_length=32),
        ),
    ]
