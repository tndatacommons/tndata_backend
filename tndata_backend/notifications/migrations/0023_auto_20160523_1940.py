# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0022_auto_20160401_1716'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gcmdevice',
            name='is_active',
        ),
        migrations.AddField(
            model_name='gcmdevice',
            name='device_type',
            field=models.CharField(default='android', choices=[('android', 'Android'), ('ios', 'iOS')], help_text='Type of device', max_length=32),
        ),
    ]
