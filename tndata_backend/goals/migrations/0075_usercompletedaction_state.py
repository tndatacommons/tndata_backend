# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0074_auto_20150909_2122'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercompletedaction',
            name='state',
            field=models.CharField(default='completed', max_length=32, choices=[('completed', 'Completed'), ('dismissed', 'Dismissed'), ('snoozed', 'Snoozed')]),
        ),
    ]
