# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_likertquestion_likertresponse'),
    ]

    operations = [
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('category', models.CharField(choices=[('lifegoal', 'Life Goal')], max_length=32)),
                ('text', models.TextField(unique=True, help_text='The text of a User-Goal')),
                ('description', models.TextField(help_text='Optional Description', blank=True)),
                ('order', models.IntegerField(default=0, help_text='Ordering of questions')),
            ],
            options={
                'verbose_name': 'Goal',
                'verbose_name_plural': 'Goals',
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='likertquestion',
            name='goal',
            field=models.ForeignKey(to='survey.Goal', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='likertresponse',
            name='selected_option',
            field=models.PositiveIntegerField(choices=[(1, 'Strongly Disagree'), (2, 'Disagree'), (3, 'Neither Agree nor Disagree'), (4, 'Agree'), (5, 'Strongly Agree')]),
            preserve_default=True,
        ),
    ]
