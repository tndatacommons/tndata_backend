# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_auto_20150512_0920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gcmmessage',
            name='message_id',
            field=models.CharField(help_text='Unique ID for this message.', db_index=True, max_length=32, blank=True),
        ),
    ]
