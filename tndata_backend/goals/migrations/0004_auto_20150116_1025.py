# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0003_auto_20150107_1349'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='name_slug',
            field=models.SlugField(max_length=128, unique=True, default='asdf'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=128, unique=True, db_index=True),
            preserve_default=True,
        ),
    ]
