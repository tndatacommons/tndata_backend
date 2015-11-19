# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0094_auto_20151112_2220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='color',
            field=models.CharField(default='#2E7D32', max_length=7, help_text='Select the color for this Category'),
        ),
        migrations.AlterField(
            model_name='category',
            name='secondary_color',
            field=models.CharField(default='#4CAF50', max_length=7, blank=True, help_text='Select a secondary color for this Category. If omitted, a complementary color will be generated.'),
        ),
    ]
