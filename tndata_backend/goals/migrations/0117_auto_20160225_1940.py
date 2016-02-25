# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0116_dailyprogress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='name',
            field=models.CharField(db_index=True, max_length=128, blank=True, help_text='A human-friendly name for this trigger'),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='name_slug',
            field=models.SlugField(max_length=128, blank=True),
        ),
    ]
