# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0051_auto_20150623_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='secondary_color',
            field=models.CharField(max_length=7, help_text='Select a secondary color for this Category. If omitted, a complementary color will be generated.', blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='color',
            field=models.CharField(default='#2ECC71', help_text='Select the color for this Category', max_length=7),
        ),
    ]
