# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0068_auto_20150814_2206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='more_info',
            field=models.TextField(blank=True, help_text='Optional tips and tricks or other small, associated ideas. Consider using bullets.'),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='more_info',
            field=models.TextField(blank=True, help_text='Optional tips and tricks or other small, associated ideas. Consider using bullets.'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='more_info',
            field=models.TextField(blank=True, help_text='Optional tips and tricks or other small, associated ideas. Consider using bullets.'),
        ),
    ]
