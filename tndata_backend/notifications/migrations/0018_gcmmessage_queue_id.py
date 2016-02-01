# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0017_auto_20151217_2000'),
    ]

    operations = [
        migrations.AddField(
            model_name='gcmmessage',
            name='queue_id',
            field=models.CharField(max_length=128, default='', blank=True),
        ),
    ]
