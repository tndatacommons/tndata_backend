# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_openendedquestion_openendedresponse'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='likertquestion',
            options={'verbose_name_plural': 'Likert Questions', 'verbose_name': 'Likert Question'},
        ),
        migrations.AlterModelOptions(
            name='multiplechoicequestion',
            options={'verbose_name_plural': 'Multiple Choice Questions', 'verbose_name': 'Multiple Choice Question'},
        ),
        migrations.AlterModelOptions(
            name='openendedquestion',
            options={'verbose_name_plural': 'Open-Ended Questions', 'verbose_name': 'Open-Ended Question'},
        ),
    ]
