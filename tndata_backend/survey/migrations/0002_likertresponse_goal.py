# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='likertresponse',
            name='goal',
            field=models.ForeignKey(default=1, to='survey.Goal'),
            preserve_default=False,
        ),
    ]
