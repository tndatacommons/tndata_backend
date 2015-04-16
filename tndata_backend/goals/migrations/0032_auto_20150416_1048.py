# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0031_auto_20150414_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.ImageField(upload_to='goals/category/images', null=True, help_text='A Hero image to be displayed at the top of the Category pager', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.ImageField(upload_to='goals/category', null=True, help_text='Upload a square icon to be displayed for the Category.', blank=True),
            preserve_default=True,
        ),
    ]
