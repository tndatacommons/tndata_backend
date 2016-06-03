# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0022_set_maximum_daily_notifications_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='app_logins',
            field=models.IntegerField(help_text='Number of times the user has logged into the app.', default=0),
        ),
    ]
