# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0085_auto_20151012_2048'),
    ]

    operations = [
        migrations.AddField(
            model_name='goalprogress',
            name='daily_checkin',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='monthly_checkin',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='goalprogress',
            name='weekly_checkin',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='current_score',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='current_total',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='max_total',
            field=models.FloatField(default=0),
        ),
    ]
