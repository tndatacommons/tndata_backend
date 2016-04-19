# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0020_userprofile_ip_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='maximum_daily_notifications',
            field=models.IntegerField(default=5, blank=True),
        ),
    ]
