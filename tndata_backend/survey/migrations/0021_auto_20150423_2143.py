# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0020_auto_20150422_1248'),
    ]

    operations = [
        migrations.AddField(
            model_name='binaryquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(blank=True, max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')]), help_text='You can apply any number of labels to this question', size=None),
        ),
        migrations.AddField(
            model_name='binaryquestion',
            name='subscale',
            field=models.IntegerField(default=0, db_index=True, help_text='Optional: Select a Subscale for this question', choices=[(0, 'None'), (1, 'Importance'), (2, 'Satisfaction')]),
        ),
        migrations.AddField(
            model_name='likertquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(blank=True, max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')]), help_text='You can apply any number of labels to this question', size=None),
        ),
        migrations.AddField(
            model_name='likertquestion',
            name='subscale',
            field=models.IntegerField(default=0, db_index=True, help_text='Optional: Select a Subscale for this question', choices=[(0, 'None'), (1, 'Importance'), (2, 'Satisfaction')]),
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(blank=True, max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')]), help_text='You can apply any number of labels to this question', size=None),
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='subscale',
            field=models.IntegerField(default=0, db_index=True, help_text='Optional: Select a Subscale for this question', choices=[(0, 'None'), (1, 'Importance'), (2, 'Satisfaction')]),
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='labels',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(blank=True, max_length=32, choices=[('family', 'Family'), ('health', 'Health'), ('skills', 'Skills'), ('success', 'Success')]), help_text='You can apply any number of labels to this question', size=None),
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='subscale',
            field=models.IntegerField(default=0, db_index=True, help_text='Optional: Select a Subscale for this question', choices=[(0, 'None'), (1, 'Importance'), (2, 'Satisfaction')]),
        ),
    ]
