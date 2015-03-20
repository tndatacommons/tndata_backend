# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0009_auto_20150320_1813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instrument',
            name='title',
            field=models.CharField(max_length=128, db_index=True, unique=True),
            preserve_default=True,
        ),
    ]
