# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0010_auto_20150302_1140'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interestgroup',
            name='category',
        ),
        migrations.RemoveField(
            model_name='interestgroup',
            name='interests',
        ),
        migrations.DeleteModel(
            name='InterestGroup',
        ),
    ]
