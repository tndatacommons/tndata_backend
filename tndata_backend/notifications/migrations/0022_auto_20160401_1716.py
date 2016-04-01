# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0021_remove_dupcliate_devices'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gcmdevice',
            options={'get_latest_by': 'updated_on', 'ordering': ['user', '-created_on', 'registration_id'], 'verbose_name_plural': 'GCM Devices', 'verbose_name': 'GCM Device'},
        ),
        migrations.AlterUniqueTogether(
            name='gcmdevice',
            unique_together=set([('registration_id', 'user', 'device_id')]),
        ),
    ]
