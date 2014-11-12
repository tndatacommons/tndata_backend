# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LikertQuestion',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('text', models.TextField(unique=True, help_text='The text of the question')),
                ('order', models.IntegerField(default=0, help_text='Ordering of questions')),
                ('available', models.BooleanField(default=True, help_text='Available to Users')),
            ],
            options={
                'verbose_name': 'Likert Question',
                'ordering': ['order'],
                'verbose_name_plural': 'Likert Questions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LikertResponse',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('selected_option', models.PositiveIntegerField(choices=[('Strongly Disagree', 1), ('Disagree', 2), ('Neither Agree nor Disagree', 3), ('Agree', 4), ('Strongly Agree', 5)])),
                ('submitted_on', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(to='survey.LikertQuestion')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Multiple Choice Response',
                'verbose_name_plural': 'Multiple Choice Responses',
            },
            bases=(models.Model,),
        ),
    ]
