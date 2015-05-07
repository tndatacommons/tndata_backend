# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_squashed_0003_auto_20150401_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gcmmessage',
            name='response_text',
            field=models.TextField(help_text='text of the response sent to GCM.', blank=True),
        ),
    ]
