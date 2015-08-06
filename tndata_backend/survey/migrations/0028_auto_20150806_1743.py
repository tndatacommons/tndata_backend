# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0027_auto_20150522_1728'),
    ]

    operations = [
        migrations.AlterField(
            model_name='binaryquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(size=None, blank=True, default=[], help_text='You can apply any number of labels to this question', base_field=models.CharField(max_length=32, choices=[('community', 'Community'), ('education', 'Education'), ('family', 'Family'), ('fun', 'Fun'), ('happiness', 'Happiness'), ('health', 'Health'), ('home', 'Home'), ('parenting', 'Parenting'), ('prosperity', 'Prosperity'), ('romance', 'Romance'), ('safety', 'Safety'), ('skills', 'Skills'), ('wellness', 'Wellness'), ('work', 'Work')], blank=True)),
        ),
        migrations.AlterField(
            model_name='likertquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(size=None, blank=True, default=[], help_text='You can apply any number of labels to this question', base_field=models.CharField(max_length=32, choices=[('community', 'Community'), ('education', 'Education'), ('family', 'Family'), ('fun', 'Fun'), ('happiness', 'Happiness'), ('health', 'Health'), ('home', 'Home'), ('parenting', 'Parenting'), ('prosperity', 'Prosperity'), ('romance', 'Romance'), ('safety', 'Safety'), ('skills', 'Skills'), ('wellness', 'Wellness'), ('work', 'Work')], blank=True)),
        ),
        migrations.AlterField(
            model_name='multiplechoicequestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(size=None, blank=True, default=[], help_text='You can apply any number of labels to this question', base_field=models.CharField(max_length=32, choices=[('community', 'Community'), ('education', 'Education'), ('family', 'Family'), ('fun', 'Fun'), ('happiness', 'Happiness'), ('health', 'Health'), ('home', 'Home'), ('parenting', 'Parenting'), ('prosperity', 'Prosperity'), ('romance', 'Romance'), ('safety', 'Safety'), ('skills', 'Skills'), ('wellness', 'Wellness'), ('work', 'Work')], blank=True)),
        ),
        migrations.AlterField(
            model_name='openendedquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(size=None, blank=True, default=[], help_text='You can apply any number of labels to this question', base_field=models.CharField(max_length=32, choices=[('community', 'Community'), ('education', 'Education'), ('family', 'Family'), ('fun', 'Fun'), ('happiness', 'Happiness'), ('health', 'Health'), ('home', 'Home'), ('parenting', 'Parenting'), ('prosperity', 'Prosperity'), ('romance', 'Romance'), ('safety', 'Safety'), ('skills', 'Skills'), ('wellness', 'Wellness'), ('work', 'Work')], blank=True)),
        ),
        migrations.AlterField(
            model_name='surveyresult',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(size=None, blank=True, default=[], help_text='The labels from the associated questions in this instrument', base_field=models.CharField(max_length=32, choices=[('community', 'Community'), ('education', 'Education'), ('family', 'Family'), ('fun', 'Fun'), ('happiness', 'Happiness'), ('health', 'Health'), ('home', 'Home'), ('parenting', 'Parenting'), ('prosperity', 'Prosperity'), ('romance', 'Romance'), ('safety', 'Safety'), ('skills', 'Skills'), ('wellness', 'Wellness'), ('work', 'Work')], blank=True)),
        ),
    ]
