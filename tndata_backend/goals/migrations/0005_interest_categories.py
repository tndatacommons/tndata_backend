# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0004_auto_20150209_1723'),
    ]

    operations = [
        migrations.AddField(
            model_name='interest',
            name='categories',
            field=models.ManyToManyField(null=True, help_text='Select Categories in which this Interest belongs.', to='goals.Category', blank=True),
            preserve_default=True,
        ),
    ]
