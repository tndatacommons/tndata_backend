# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0016_auto_20150304_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.CharField(max_length=128, db_index=True, unique=True, help_text='A Title for the Category.'),
            preserve_default=True,
        ),
    ]
