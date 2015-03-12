# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0018_auto_20150312_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='behavioraction',
            name='title_slug',
            field=models.SlugField(max_length=128, default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behaviorsequence',
            name='title_slug',
            field=models.SlugField(max_length=128, default=''),
            preserve_default=True,
        ),
    ]
