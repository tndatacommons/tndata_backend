# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0007_auto_20150210_2233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='text',
            field=models.CharField(blank=True, help_text='The Trigger text shown to the user.', max_length=140),
            preserve_default=True,
        ),
    ]
