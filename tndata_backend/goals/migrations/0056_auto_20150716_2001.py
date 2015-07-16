# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0055_auto_20150716_1833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='title',
            field=models.CharField(db_index=True, help_text='A short (50 character) title for this Action', max_length=256),
        ),
        migrations.AlterField(
            model_name='action',
            name='title_slug',
            field=models.SlugField(max_length=256),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='title',
            field=models.CharField(unique=True, db_index=True, max_length=256, help_text='A unique title for this Behavior (50 characters)'),
        ),
    ]
