# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0016_auto_20151028_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gcmmessage',
            name='response_data',
            field=jsonfield.fields.JSONField(blank=True, help_text='The response data we get from GCM after it delivers this', default=dict),
        ),
    ]
