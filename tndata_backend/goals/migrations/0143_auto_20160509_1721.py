# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0142_auto_20160428_1858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useraction',
            options={'verbose_name': 'User Action', 'ordering': ['user', 'next_trigger_date', 'action'], 'verbose_name_plural': 'User Actions'},
        ),
    ]
