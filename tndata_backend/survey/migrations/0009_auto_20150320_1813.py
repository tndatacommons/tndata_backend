# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0008_instrument'),
    ]

    operations = [
        migrations.AddField(
            model_name='likertquestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', to='survey.Instrument', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', to='survey.Instrument', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='instruments',
            field=models.ManyToManyField(help_text='The Instrument(s) to which this question belongs.', to='survey.Instrument', blank=True, null=True),
            preserve_default=True,
        ),
    ]
