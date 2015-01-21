# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0002_auto_20150121_1614'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='icon',
            field=models.ImageField(upload_to='goals/action', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.ImageField(upload_to='goals/category', blank=True, null=True),
            preserve_default=True,
        ),
    ]
