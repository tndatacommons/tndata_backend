# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0056_auto_20150716_2001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(default='custom', max_length=32, db_index=True, choices=[('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource'), ('now', 'Do it now'), ('later', 'Do it later'), ('custom', 'Custom')]),
        ),
    ]
