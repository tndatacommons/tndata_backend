# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0105_pre_serializer_useractions_usergoals'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='serialized_trigger',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
    ]
