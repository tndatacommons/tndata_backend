# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gcmmessage',
            name='scheduled',
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='success',
            field=models.NullBooleanField(),
            preserve_default=True,
        ),
    ]
