# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0123_auto_20160307_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='bucket',
            field=models.CharField(max_length=32, blank=True, help_text='The "bucket" from which this object is selected when queueing up notifications.', default='core'),
        ),
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(max_length=32, db_index=True, choices=[('reinforcing', ''), ('enabling', ''), ('showing', ''), ('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource Notification'), ('now', 'Do it now'), ('later', 'Do it later'), ('asking', 'Checkup Notification')], default='showing'),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='frequency',
            field=models.CharField(max_length=32, blank=True, null=True, choices=[('daily', 'Daily'), ('weekly', 'Once a week'), ('biweekly', 'A couple times a week'), ('multiweekly', 'Three - four times a week'), ('weekends', 'During the weekend'), ('monthly', 'Once a month')], help_text='Select a frequency to determine how often a reminder should be sent.'),
        ),
    ]
