# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('survey', '0024_remove_prior_survey_labels'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyResult',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('labels', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32, choices=[('happiness', 'Happiness'), ('community', 'Community'), ('family', 'Family'), ('home', 'Home'), ('romance', 'Romance'), ('health', 'Health'), ('wellness', 'Wellness'), ('safety', 'Safety'), ('parenting', 'Parenting'), ('education', 'Education'), ('skills', 'Skills'), ('work', 'Work'), ('prosperity', 'Prosperity'), ('fun', 'Fun'), ('needs-work', 'Needs work'), ('focus', 'Focus')], blank=True), help_text='The labels from the associated questions in this instrument', default=[], size=None, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('instrument', models.ForeignKey(to='survey.Instrument')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Survey Results',
                'verbose_name': 'Survey Result',
                'ordering': ['-created_on'],
            },
        ),
        migrations.AlterModelOptions(
            name='binaryresponse',
            options={'verbose_name_plural': 'Binary Responses', 'get_latest_by': 'submitted_on', 'verbose_name': 'Binary Response'},
        ),
        migrations.AlterModelOptions(
            name='likertresponse',
            options={'verbose_name_plural': 'Likert Responses', 'get_latest_by': 'submitted_on', 'verbose_name': 'Likert Response'},
        ),
        migrations.AlterModelOptions(
            name='multiplechoiceresponse',
            options={'verbose_name_plural': 'Multiple Choice Responses', 'get_latest_by': 'submitted_on', 'verbose_name': 'Multiple Choice Response'},
        ),
        migrations.AlterModelOptions(
            name='openendedresponse',
            options={'verbose_name_plural': 'Open-Ended Responses', 'get_latest_by': 'submitted_on', 'verbose_name': 'Open-Ended Response'},
        ),
    ]
