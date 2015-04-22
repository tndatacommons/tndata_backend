# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0019_create_survey_admin_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='binaryquestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', blank=True, to='survey.Instrument'),
        ),
        migrations.AlterField(
            model_name='likertquestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', blank=True, to='survey.Instrument'),
        ),
        migrations.AlterField(
            model_name='multiplechoicequestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', blank=True, to='survey.Instrument'),
        ),
        migrations.AlterField(
            model_name='openendedquestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', blank=True, to='survey.Instrument'),
        ),
    ]
