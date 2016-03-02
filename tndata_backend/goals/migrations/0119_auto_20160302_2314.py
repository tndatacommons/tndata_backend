# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0118_dailyprogress_goal_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(max_length=32, choices=[('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource Notification'), ('now', 'Do it now'), ('later', 'Do it later'), ('custom', 'Custom Notification')], db_index=True, default='custom'),
        ),
    ]
