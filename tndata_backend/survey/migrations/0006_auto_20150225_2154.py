# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0005_auto_20150225_2152'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='likertquestion',
            name='goal',
        ),
        migrations.RemoveField(
            model_name='likertresponse',
            name='goal',
        ),
        migrations.DeleteModel(
            name='Goal',
        ),
    ]
