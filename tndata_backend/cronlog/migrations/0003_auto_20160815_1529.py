# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cronlog', '0002_cronlog_host'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cronlog',
            options={'verbose_name_plural': 'Cron Logs', 'ordering': ['-created_on', 'command'], 'verbose_name': 'Cron Log'},
        ),
    ]
