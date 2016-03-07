# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0122_convert_custom_actions_to_core'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(db_index=True, choices=[('prep', 'Preparatory Notification'), ('core', 'Core Notification'), ('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource Notification'), ('now', 'Do it now'), ('later', 'Do it later'), ('checkup', 'Checkup Notification')], max_length=32, default='core'),
        ),
    ]
