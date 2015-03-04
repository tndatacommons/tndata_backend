# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0012_auto_20150304_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='subtitle',
            field=models.CharField(help_text='A one-liner description for this goal.', null=True, max_length=256),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='goal',
            name='title_slug',
            field=models.SlugField(null=True, max_length=256),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='goal',
            name='name',
            field=models.CharField(max_length=128, db_index=True, unique=True),
            preserve_default=True,
        ),
    ]
