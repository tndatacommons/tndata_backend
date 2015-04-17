# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0017_auto_20150408_1430'),
    ]

    operations = [
        migrations.AddField(
            model_name='openendedquestion',
            name='input_type',
            field=models.CharField(choices=[('text', 'Text'), ('datetime', 'Date/Time'), ('numeric', 'Numeric')], default='text', help_text='Select the type of data to allow for responses', max_length=32),
            preserve_default=True,
        ),
    ]
