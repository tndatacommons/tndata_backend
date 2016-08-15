# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cronlog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronlog',
            name='host',
            field=models.CharField(max_length=256, default='', blank=True),
        ),
    ]
