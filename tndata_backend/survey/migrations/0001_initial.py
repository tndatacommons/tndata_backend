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
            name='MultipleChoiceQuestion',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('text', models.TextField(unique=True, help_text='The text of the question')),
                ('order', models.IntegerField(help_text='Ordering of questions', default=0)),
                ('available', models.BooleanField(default=True, help_text='Available to Users')),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('text', models.TextField(help_text='The text of the response option')),
                ('available', models.BooleanField(default=True, help_text='Available to Users')),
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
