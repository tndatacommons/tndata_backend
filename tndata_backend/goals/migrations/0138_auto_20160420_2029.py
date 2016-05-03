# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0137_auto_20160420_1851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='frequency',
            field=models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Once a week'), ('biweekly', 'A couple times a week'), ('multiweekly', 'Three - four times a week'), ('weekends', 'During the weekend')], max_length=32, blank=True, help_text='Select a frequency to determine how often a reminder should be sent.', null=True),
        ),
    ]
