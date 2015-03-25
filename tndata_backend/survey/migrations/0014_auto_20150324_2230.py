# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0013_auto_20150324_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='likertquestion',
            name='scale',
            field=models.CharField(default='5_point_agreement', help_text='Select the Scale for this question', max_length=32),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='likertresponse',
            name='selected_option',
            field=models.PositiveIntegerField(),
            preserve_default=True,
        ),
    ]
