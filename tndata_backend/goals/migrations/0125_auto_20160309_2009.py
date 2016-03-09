# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0124_auto_20160309_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(choices=[('reinforcing', 'Reinforcing'), ('enabling', 'Enabling'), ('showing', 'Showing'), ('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource Notification'), ('now', 'Do it now'), ('later', 'Do it later'), ('asking', 'Checkup Notification')], default='showing', db_index=True, max_length=32),
        ),
    ]
