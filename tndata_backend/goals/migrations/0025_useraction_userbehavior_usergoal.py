# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0024_auto_20150313_1407'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAction',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('completed', models.BooleanField(default=False)),
                ('completed_on', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user', 'action'],
                'verbose_name_plural': 'User Actions',
                'verbose_name': 'User Action',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserBehavior',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('completed', models.BooleanField(default=False)),
                ('completed_on', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user', 'behavior'],
                'verbose_name_plural': 'User Behaviors',
                'verbose_name': 'User Behavior',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserGoal',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('completed', models.BooleanField(default=False)),
                ('completed_on', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(to='goals.Goal')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user', 'goal'],
                'verbose_name_plural': 'User Goals',
                'verbose_name': 'User Goal',
            },
            bases=(models.Model,),
        ),
    ]
