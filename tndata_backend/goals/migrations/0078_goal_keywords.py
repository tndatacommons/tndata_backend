# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0077_auto_20150929_1746'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(default=list, base_field=models.CharField(max_length=32, blank=True), size=None, blank=True, help_text='Add keywords for this goal. These will be used to generate suggestions for the user.'),
        ),
    ]
