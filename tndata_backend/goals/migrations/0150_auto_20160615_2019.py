# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0149_auto_20160614_2004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='grouping',
            field=models.IntegerField(null=True, default=-1, choices=[(-1, 'General'), (0, 'Get ready for college'), (1, 'Succeed in college'), (2, 'Help your student succeed'), (3, 'Featured')], blank=True),
        ),
    ]
