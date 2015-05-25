# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0045_auto_20150511_1518'),
    ]

    operations = [
        migrations.CreateModel(
            name='BehaviorProgress',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('status', models.IntegerField(choices=[(1, 'Off Course'), (2, 'Wandering'), (3, 'On Course')])),
                ('reported_on', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('user_behavior', models.ForeignKey(to='goals.UserBehavior')),
            ],
            options={
                'verbose_name_plural': 'Behavior Progression',
                'get_latest_by': 'reported_on',
                'verbose_name': 'Behavior Progress',
                'ordering': ['-reported_on'],
            },
        ),
        migrations.CreateModel(
            name='GoalProgress',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('current_score', models.FloatField()),
                ('current_total', models.FloatField()),
                ('max_total', models.FloatField()),
                ('reported_on', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(to='goals.Goal')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Goal Progression',
                'get_latest_by': 'reported_on',
                'verbose_name': 'Goal Progress',
                'ordering': ['-reported_on'],
            },
        ),
    ]
