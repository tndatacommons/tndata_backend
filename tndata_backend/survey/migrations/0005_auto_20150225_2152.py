# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0004_auto_20141112_2040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='likertresponse',
            name='selected_option',
            field=models.PositiveIntegerField(choices=[(1, 'Strongly Disagree'), (2, 'Disagree'), (3, 'Slightly Disagree'), (4, 'Neither Agree nor Disagree'), (5, 'Slightly Agree'), (6, 'Agree'), (7, 'Strongly Agree')]),
            preserve_default=True,
        ),
    ]
