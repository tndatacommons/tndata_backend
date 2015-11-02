# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0087_remove_place_triggers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trigger',
            name='trigger_type',
        ),
    ]
