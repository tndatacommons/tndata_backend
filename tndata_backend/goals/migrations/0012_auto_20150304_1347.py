# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0011_auto_20150304_1333'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interest',
            name='categories',
        ),
        migrations.RemoveField(
            model_name='action',
            name='interests',
        ),
        migrations.DeleteModel(
            name='Interest',
        ),
    ]
