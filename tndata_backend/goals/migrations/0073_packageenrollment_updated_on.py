# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0072_auto_20150827_1439'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageenrollment',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 8, 27, 22, 2, 14, 360452, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
