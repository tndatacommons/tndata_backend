# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0100_auto_20151216_2341'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='serialized_action',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='useraction',
            name='serialized_custom_trigger',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='useraction',
            name='serialized_primary_goal',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
    ]
