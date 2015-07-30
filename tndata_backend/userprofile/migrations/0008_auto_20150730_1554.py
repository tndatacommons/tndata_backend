# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0007_auto_20150709_2129'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='birthdate',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='children',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='economic_aspiration',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='educational_level',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='employment_status',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='gender',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='home_address',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='home_city',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='home_phone',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='home_state',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='home_zip',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='mobile_phone',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='race',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='relationship_status',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='needs_onboarding',
            field=models.BooleanField(default=False),
        ),
    ]
