# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0014_userprofile_updated_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='maximum_daily_notifications',
            field=models.IntegerField(default=10, blank=True),
        ),
    ]
