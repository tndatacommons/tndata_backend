# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0015_auto_20150325_1306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='likertquestion',
            name='scale',
            field=models.CharField(max_length=32, default='5_point_agreement', choices=[('5_point_agreement', '5 Point Agreement'), ('5_point_reverse_agreement', '5 Point Reverse Agreement'), ('7_point_agreement', '7 Point Agreement'), ('7_point_reverse_agreement', '7 Point Reverse Agreement'), ('9_point_agreement', '9 Point Agreement'), ('9_point_reverse_agreement', '9 Point Reverse Agreement'), ('5_point_frequency', '5 Point Frequency'), ('7_point_frequency', '7 Point Frequency'), ('7_point_importance', '7 Point Importance'), ('5_point_satisfaction', '5 Point Satisfaction'), ('7_point_satisfaction', '7 Point Satisfaction')], help_text='Select the Scale for this question'),
            preserve_default=True,
        ),
    ]
