# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0002_auto_20150107_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interest',
            name='max_neef_tags',
            field=djorm_pgarray.fields.TextArrayField(dbtype='text', help_text='A Comma-separated list', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='sdt_major',
            field=models.CharField(db_index=True, blank=True, help_text='The Major SDT identifier', max_length=128),
            preserve_default=True,
        ),
    ]
