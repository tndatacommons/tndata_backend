# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_auto_20150522_1736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gcmmessage',
            name='title',
            field=models.CharField(default='', max_length=256),
        ),
    ]
