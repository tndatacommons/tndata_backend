# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0150_auto_20160615_2019'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='goal',
            name='outcome',
        ),
    ]
