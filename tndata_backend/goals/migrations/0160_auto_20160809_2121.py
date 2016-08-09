# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0159_auto_20160808_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behavior',
            name='title',
            field=models.CharField(db_index=True, help_text='A title for this Behavior (~50 characters)', max_length=256),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='title_slug',
            field=models.SlugField(max_length=256),
        ),
        migrations.AlterField(
            model_name='goal',
            name='title',
            field=models.CharField(db_index=True, help_text='A Title for the Goal (50 characters)', max_length=256),
        ),
    ]
