# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0057_auto_20150716_2209'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='packaged_content',
            field=models.BooleanField(help_text='Is this Category for a collection of Packaged Content?', default=False),
        ),
    ]
