# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0146_dailyprogress_checkin_streak'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='grouping',
            field=models.IntegerField(null=True, default=-1, blank=True, choices=[(-1, 'None'), (0, 'High School'), (1, 'College'), (2, 'Parents')]),
        ),
    ]
