# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0069_auto_20150819_2231'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='external_resource_name',
            field=models.CharField(help_text='A human-friendly name for your external resource. This is especially helpful for web links.', blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='behavior',
            name='external_resource_name',
            field=models.CharField(help_text='A human-friendly name for your external resource. This is especially helpful for web links.', blank=True, max_length=256),
        ),
    ]
