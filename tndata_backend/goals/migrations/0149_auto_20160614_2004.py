# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0148_auto_20160614_1725'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='featured',
        ),
        migrations.AlterField(
            model_name='category',
            name='grouping',
            field=models.IntegerField(blank=True, default=-1, choices=[(-1, 'General'), (0, 'Get ready for college'), (1, 'Succeed in College'), (2, 'Help your student succeed'), (3, 'Featured')], null=True),
        ),
    ]
