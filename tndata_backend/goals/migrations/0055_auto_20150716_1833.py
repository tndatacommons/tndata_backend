# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0054_auto_20150716_1704'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.CharField(db_index=True, default='custom', choices=[('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource'), ('now', 'Do it now'), ('later', 'Do it later'), ('custom', 'Custom')], max_length='32'),
        ),
    ]
