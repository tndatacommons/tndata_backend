# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0014_auto_20150324_2230'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instrument',
            name='user_instructions',
        ),
        migrations.AddField(
            model_name='binaryquestion',
            name='instructions',
            field=models.CharField(blank=True, default='', help_text='Instructions for the user answering this question.', max_length=140),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='likertquestion',
            name='instructions',
            field=models.CharField(blank=True, default='', help_text='Instructions for the user answering this question.', max_length=140),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='instructions',
            field=models.CharField(blank=True, default='', help_text='Instructions for the user answering this question.', max_length=140),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='instructions',
            field=models.CharField(blank=True, default='', help_text='Instructions for the user answering this question.', max_length=140),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='likertquestion',
            name='scale',
            field=models.CharField(default='5_point_agreement', choices=[('7_point_importance', '7 Point Importance'), ('7_point_satisfaction', '7 Point Satisfaction'), ('9_point_reverse_agreement', '9 Point Reverse Agreement'), ('5_point_satisfaction', '5 Point Satisfaction'), ('9_point_agreement', '9 Point Agreement'), ('7_point_frequency', '7 Point Frequency'), ('5_point_agreement', '5 Point Agreement'), ('7_point_agreement', '7 Point Agreement'), ('5_point_reverse_agreement', '5 Point Reverse Agreement'), ('7_point_reverse_agreement', '7 Point Reverse Agreement'), ('5_point_frequency', '5 Point Frequency')], help_text='Select the Scale for this question', max_length=32),
            preserve_default=True,
        ),
    ]
