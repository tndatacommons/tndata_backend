# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0020_populate_basebehavior_title_slugs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='behavioraction',
            name='name',
        ),
        migrations.RemoveField(
            model_name='behavioraction',
            name='name_slug',
        ),
        migrations.RemoveField(
            model_name='behaviorsequence',
            name='name',
        ),
        migrations.RemoveField(
            model_name='behaviorsequence',
            name='name_slug',
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='title_slug',
            field=models.SlugField(max_length=256, unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='title_slug',
            field=models.SlugField(max_length=256, unique=True),
            preserve_default=True,
        ),
    ]
