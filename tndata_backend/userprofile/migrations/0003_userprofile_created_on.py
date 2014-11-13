# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0002_auto_20141113_1617'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 13, 22, 19, 27, 292506), auto_now_add=True),
            preserve_default=False,
        ),
    ]
