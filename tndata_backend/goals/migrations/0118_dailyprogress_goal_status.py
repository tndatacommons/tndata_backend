# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0117_auto_20160225_1940'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyprogress',
            name='goal_status',
            field=jsonfield.fields.JSONField(default=dict, help_text='User feedback on their progress toward achieving goals', blank=True),
        ),
    ]
