# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('survey', '0011_instrument_user_instructions'),
    ]

    operations = [
        migrations.CreateModel(
            name='BinaryQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('text', models.TextField(help_text='The text of the question', unique=True)),
                ('order', models.IntegerField(help_text='Ordering of questions', default=0)),
                ('available', models.BooleanField(help_text='Available to Users', default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('instruments', models.ManyToManyField(blank=True, null=True, to='survey.Instrument', help_text='The Instrument(s) to which this question belongs.')),
            ],
            options={
                'verbose_name': 'Binary Question',
                'verbose_name_plural': 'Binary Questions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BinaryResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('selected_option', models.BooleanField(default=False)),
                ('submitted_on', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(to='survey.BinaryQuestion')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Binary Response',
                'verbose_name_plural': 'Binary Responses',
            },
            bases=(models.Model,),
        ),
    ]
