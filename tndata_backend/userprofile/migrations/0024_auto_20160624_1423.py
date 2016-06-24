# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0023_userprofile_app_logins'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='maximum_daily_notifications',
            field=models.IntegerField(blank=True, default=3),
        ),
    ]
