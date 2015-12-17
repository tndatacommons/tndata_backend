# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0101_auto_20151217_2001'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='serialized_behavior',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
    ]
