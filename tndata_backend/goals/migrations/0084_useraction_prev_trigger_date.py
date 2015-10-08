# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0083_auto_20151007_1748'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='prev_trigger_date',
            field=models.DateTimeField(null=True),
        ),
    ]
