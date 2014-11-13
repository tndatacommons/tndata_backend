# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('survey', '0002_likertresponse_goal'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpenEndedQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('text', models.TextField(help_text='The text of the question', unique=True)),
                ('order', models.IntegerField(default=0, help_text='Ordering of questions')),
                ('available', models.BooleanField(default=True, help_text='Available to Users')),
            ],
            options={
                'verbose_name': 'Open-Ended Question',
                'verbose_name_plural': 'Open-Ended Questions',
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OpenEndedResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('response', models.TextField()),
                ('submitted_on', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(to='survey.OpenEndedQuestion')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Open-Ended Response',
                'verbose_name_plural': 'Open-Ended Responses',
            },
            bases=(models.Model,),
        ),
    ]
