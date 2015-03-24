# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0010_auto_20150320_1825'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='user_instructions',
            field=models.TextField(blank=True, help_text='A (very) short set of instructions for all questions within this Instrument', default=''),
            preserve_default=True,
        ),
    ]
