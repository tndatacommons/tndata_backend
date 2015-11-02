# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0088_remove_trigger_trigger_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trigger',
            name='location',
        ),
    ]
