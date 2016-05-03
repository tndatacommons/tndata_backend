# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0139_reset_montly_frequencies'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='updated_on',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 26, 18, 4, 58, 692802, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userbehavior',
            name='updated_on',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 26, 18, 5, 2, 173238, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usercategory',
            name='updated_on',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 26, 18, 5, 6, 229293, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usergoal',
            name='updated_on',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 26, 18, 5, 11, 404946, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
