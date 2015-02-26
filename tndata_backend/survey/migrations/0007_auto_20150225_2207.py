# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0006_auto_20150225_2154'),
    ]

    new_time = datetime.datetime(2015, 2, 26, 4, 6, 0, 0, tzinfo=utc)
    operations = [
        migrations.AddField(
            model_name='likertquestion',
            name='created',
            field=models.DateTimeField(default=new_time, auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='likertquestion',
            name='updated',
            field=models.DateTimeField(default=new_time, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='created',
            field=models.DateTimeField(default=new_time, auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='updated',
            field=models.DateTimeField(default=new_time, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='created',
            field=models.DateTimeField(default=new_time, auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='updated',
            field=models.DateTimeField(default=new_time, auto_now=True),
            preserve_default=False,
        ),
    ]
