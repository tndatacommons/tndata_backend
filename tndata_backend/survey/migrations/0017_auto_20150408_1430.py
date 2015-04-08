# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0016_auto_20150408_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='instructions',
            field=models.CharField(help_text='Instructions for the user answering this question. NOTE: Each question also has an instructions field. The information here will only be used if you do not provide instructions on the question', default='', max_length=140, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='likertquestion',
            name='scale',
            field=models.CharField(choices=[('5_point_agreement', '5 Point Agreement'), ('5_point_reverse_agreement', '5 Point Reverse Agreement'), ('7_point_agreement', '7 Point Agreement'), ('7_point_reverse_agreement', '7 Point Reverse Agreement'), ('9_point_agreement', '9 Point Agreement'), ('9_point_reverse_agreement', '9 Point Reverse Agreement'), ('5_point_frequency', '5 Point Frequency'), ('7_point_frequency', '7 Point Frequency'), ('7_point_importance', '7 Point Importance'), ('5_point_satisfaction', '5 Point Satisfaction'), ('7_point_satisfaction', '7 Point Satisfaction'), ('5_point_necessary', '5 Point Necessary')], help_text='Select the Scale for this question', default='5_point_agreement', max_length=32),
            preserve_default=True,
        ),
    ]
