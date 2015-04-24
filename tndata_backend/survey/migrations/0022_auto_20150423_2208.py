# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0021_auto_20150423_2143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='binaryquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')], blank=True), help_text='You can apply any number of labels to this question', default=[], size=None, blank=True),
        ),
        migrations.AlterField(
            model_name='likertquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')], blank=True), help_text='You can apply any number of labels to this question', default=[], size=None, blank=True),
        ),
        migrations.AlterField(
            model_name='multiplechoicequestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')], blank=True), help_text='You can apply any number of labels to this question', default=[], size=None, blank=True),
        ),
        migrations.AlterField(
            model_name='openendedquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')], blank=True), help_text='You can apply any number of labels to this question', default=[], size=None, blank=True),
        ),
    ]
