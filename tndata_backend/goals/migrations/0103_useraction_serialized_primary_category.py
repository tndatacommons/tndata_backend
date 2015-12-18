# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0102_useraction_serialized_behavior'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='serialized_primary_category',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
    ]
