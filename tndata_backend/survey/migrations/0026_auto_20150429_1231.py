# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0025_auto_20150428_1018'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='surveyresult',
            options={'ordering': ['-created_on', 'score'], 'verbose_name_plural': 'Survey Results', 'verbose_name': 'Survey Result', 'get_latest_by': 'created_on'},
        ),
    ]
