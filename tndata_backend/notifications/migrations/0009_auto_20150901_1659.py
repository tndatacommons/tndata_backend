# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0008_auto_20150527_1054'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gcmdevice',
            options={'ordering': ['user', '-created_on', 'registration_id'], 'verbose_name': 'GCM Device', 'verbose_name_plural': 'GCM Devices'},
        ),
        migrations.AlterModelOptions(
            name='gcmmessage',
            options={'ordering': ['success', '-deliver_on', '-created_on'], 'verbose_name': 'GCM Message', 'verbose_name_plural': 'GCM Messages'},
        ),
    ]
