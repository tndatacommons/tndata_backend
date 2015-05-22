# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0026_auto_20150429_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='binaryquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(help_text='You can apply any number of labels to this question', size=None, blank=True, default=[], base_field=models.CharField(choices=[('happiness', 'Happiness'), ('community', 'Community'), ('family', 'Family'), ('home', 'Home'), ('romance', 'Romance'), ('health', 'Health'), ('wellness', 'Wellness'), ('safety', 'Safety'), ('parenting', 'Parenting'), ('education', 'Education'), ('skills', 'Skills'), ('work', 'Work'), ('prosperity', 'Prosperity'), ('fun', 'Fun')], blank=True, max_length=32)),
        ),
        migrations.AlterField(
            model_name='likertquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(help_text='You can apply any number of labels to this question', size=None, blank=True, default=[], base_field=models.CharField(choices=[('happiness', 'Happiness'), ('community', 'Community'), ('family', 'Family'), ('home', 'Home'), ('romance', 'Romance'), ('health', 'Health'), ('wellness', 'Wellness'), ('safety', 'Safety'), ('parenting', 'Parenting'), ('education', 'Education'), ('skills', 'Skills'), ('work', 'Work'), ('prosperity', 'Prosperity'), ('fun', 'Fun')], blank=True, max_length=32)),
        ),
        migrations.AlterField(
            model_name='multiplechoicequestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(help_text='You can apply any number of labels to this question', size=None, blank=True, default=[], base_field=models.CharField(choices=[('happiness', 'Happiness'), ('community', 'Community'), ('family', 'Family'), ('home', 'Home'), ('romance', 'Romance'), ('health', 'Health'), ('wellness', 'Wellness'), ('safety', 'Safety'), ('parenting', 'Parenting'), ('education', 'Education'), ('skills', 'Skills'), ('work', 'Work'), ('prosperity', 'Prosperity'), ('fun', 'Fun')], blank=True, max_length=32)),
        ),
        migrations.AlterField(
            model_name='openendedquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(help_text='You can apply any number of labels to this question', size=None, blank=True, default=[], base_field=models.CharField(choices=[('happiness', 'Happiness'), ('community', 'Community'), ('family', 'Family'), ('home', 'Home'), ('romance', 'Romance'), ('health', 'Health'), ('wellness', 'Wellness'), ('safety', 'Safety'), ('parenting', 'Parenting'), ('education', 'Education'), ('skills', 'Skills'), ('work', 'Work'), ('prosperity', 'Prosperity'), ('fun', 'Fun')], blank=True, max_length=32)),
        ),
        migrations.AlterField(
            model_name='surveyresult',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(help_text='The labels from the associated questions in this instrument', size=None, blank=True, default=[], base_field=models.CharField(choices=[('happiness', 'Happiness'), ('community', 'Community'), ('family', 'Family'), ('home', 'Home'), ('romance', 'Romance'), ('health', 'Health'), ('wellness', 'Wellness'), ('safety', 'Safety'), ('parenting', 'Parenting'), ('education', 'Education'), ('skills', 'Skills'), ('work', 'Work'), ('prosperity', 'Prosperity'), ('fun', 'Fun')], blank=True, max_length=32)),
        ),
    ]
