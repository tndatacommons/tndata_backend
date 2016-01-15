# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0109_auto_20160115_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='serialized_default_trigger',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
    ]
