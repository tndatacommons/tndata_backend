# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0115_auto_20160223_2354'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyProgress',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('actions_total', models.IntegerField(help_text='Total number of actions for the user on this day', default=0)),
                ('actions_completed', models.IntegerField(help_text='Number of actions the user completed', default=0)),
                ('actions_snoozed', models.IntegerField(help_text='Number of actions the user snoozed', default=0)),
                ('actions_dismissed', models.IntegerField(help_text='Number of actions the user dismissed', default=0)),
                ('customactions_total', models.IntegerField(help_text='Total number of custom actions for the user on this day', default=0)),
                ('customactions_completed', models.IntegerField(help_text='Number of custom actions the user completed', default=0)),
                ('customactions_snoozed', models.IntegerField(help_text='Number of custom actions the user snoozed', default=0)),
                ('customactions_dismissed', models.IntegerField(help_text='Number of custom actions the user dismissed', default=0)),
                ('behaviors_total', models.IntegerField(help_text='Total number of behaviors selected on this day', default=0)),
                ('behaviors_status', jsonfield.fields.JSONField(help_text="Describes the user's status on work toward this behavior", blank=True, default=dict)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Daily Progress',
                'ordering': ['-updated_on', 'user'],
                'verbose_name_plural': 'Daily Progresses',
                'get_latest_by': 'updated_on',
            },
        ),
    ]
