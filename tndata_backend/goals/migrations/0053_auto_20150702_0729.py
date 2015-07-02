# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0052_auto_20150701_1818'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='more_info',
            field=models.TextField(help_text='Persuasive narrative description: Tell the user why this is important.', blank=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='more_info',
            field=models.TextField(help_text='Persuasive narrative description: Tell the user why this is important.', blank=True),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='more_info',
            field=models.TextField(help_text='Persuasive narrative description: Tell the user why this is important.', blank=True),
        ),
    ]
