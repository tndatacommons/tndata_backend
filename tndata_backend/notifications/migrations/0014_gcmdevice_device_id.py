# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0013_auto_20150901_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='gcmdevice',
            name='device_id',
            field=models.CharField(help_text='Some unique ID for a device. This is used to help update the registration_id for individual users.', max_length=64, null=True, blank=True),
        ),
    ]
