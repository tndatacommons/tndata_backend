# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0037_goal_notes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='behavior',
            name='categories',
        ),
    ]
