# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('category', models.CharField(max_length=32, choices=[('lifegoal', 'Life Goal')])),
                ('text', models.TextField(help_text='The text of a User-Goal', unique=True)),
                ('description', models.TextField(blank=True, help_text='Optional Description')),
                ('order', models.IntegerField(help_text='Ordering of questions', default=0)),
            ],
            options={
                'verbose_name_plural': 'Goals',
                'ordering': ['order'],
                'verbose_name': 'Goal',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LikertQuestion',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('text', models.TextField(help_text='The text of the question', unique=True)),
                ('order', models.IntegerField(help_text='Ordering of questions', default=0)),
                ('available', models.BooleanField(help_text='Available to Users', default=True)),
                ('goal', models.ManyToManyField(to='survey.Goal', help_text='Attach this question to one or more Goals', null=True)),
            ],
            options={
                'verbose_name_plural': 'Likert Questions',
                'ordering': ['order'],
                'verbose_name': 'Likert Question',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LikertResponse',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('selected_option', models.PositiveIntegerField(choices=[(1, 'Strongly Disagree'), (2, 'Disagree'), (3, 'Neither Agree nor Disagree'), (4, 'Agree'), (5, 'Strongly Agree')])),
                ('submitted_on', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(to='survey.LikertQuestion')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Likert Responses',
                'verbose_name': 'Likert Response',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultipleChoiceQuestion',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('text', models.TextField(help_text='The text of the question', unique=True)),
                ('order', models.IntegerField(help_text='Ordering of questions', default=0)),
                ('available', models.BooleanField(help_text='Available to Users', default=True)),
            ],
            options={
                'verbose_name_plural': 'Multiple Choice Questions',
                'ordering': ['order'],
                'verbose_name': 'Multiple Choice Question',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultipleChoiceResponse',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('submitted_on', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(to='survey.MultipleChoiceQuestion')),
            ],
            options={
                'verbose_name_plural': 'Multiple Choice Responses',
                'verbose_name': 'Multiple Choice Response',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultipleChoiceResponseOption',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('text', models.TextField(help_text='The text of the response option')),
                ('available', models.BooleanField(help_text='Available to Users', default=True)),
                ('question', models.ForeignKey(to='survey.MultipleChoiceQuestion')),
            ],
            options={
                'verbose_name_plural': 'Multiple Choice Response Options',
                'verbose_name': 'Multiple Choice Response Option',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='multiplechoiceresponseoption',
            unique_together=set([('question', 'text')]),
        ),
        migrations.AlterOrderWithRespectTo(
            name='multiplechoiceresponseoption',
            order_with_respect_to='question',
        ),
        migrations.AddField(
            model_name='multiplechoiceresponse',
            name='selected_option',
            field=models.ForeignKey(to='survey.MultipleChoiceResponseOption'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiplechoiceresponse',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
