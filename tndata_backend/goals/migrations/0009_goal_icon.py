# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0008_auto_20150211_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='icon',
            field=models.ImageField(upload_to='goals/goal', blank=True, null=True, help_text='Upload an image to be displayed next to the Goal.'),
            preserve_default=True,
        ),
    ]
