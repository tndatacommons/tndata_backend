# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0036_auto_20150427_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='notes',
            field=models.TextField(blank=True, help_text='Misc notes about this item. This is for your use and will not be displayed in the app.', null=True),
        ),
    ]
