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
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('summary', models.TextField()),
                ('description', models.TextField()),
                ('default_reminder_time', models.TimeField(blank=True, null=True)),
                ('default_reminder_frequency', models.CharField(max_length=10, blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')])),
            ],
            options={
                'verbose_name_plural': 'Action',
                'ordering': ['order', 'name'],
                'verbose_name': 'Action',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionTaken',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('date_completed', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name_plural': 'Actions Taken',
                'ordering': ['date_completed', 'selected_action', 'user'],
                'verbose_name': 'Action Taken',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Category',
                'ordering': ['order', 'name'],
                'verbose_name': 'Category',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomReminder',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('time', models.TimeField(blank=True, null=True)),
                ('frequency', models.CharField(max_length=10, blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')])),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Custom Reminders',
                'ordering': ['action', 'user', 'time'],
                'verbose_name': 'Custom Reminder',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Interest',
                'ordering': ['order', 'name'],
                'verbose_name': 'Interest',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterestGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('public', models.BooleanField(default=True)),
                ('category', models.ForeignKey(to='goals.Category')),
                ('interests', models.ManyToManyField(to='goals.Interest', blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Interest Groups',
                'verbose_name': 'Interest Group',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedAction',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('date_selected', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Selected Actions',
                'ordering': ['date_selected'],
                'verbose_name': 'Selected Action',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='customreminder',
            unique_together=set([('user', 'action')]),
        ),
        migrations.AddField(
            model_name='actiontaken',
            name='selected_action',
            field=models.ForeignKey(to='goals.SelectedAction'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actiontaken',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='interests',
            field=models.ManyToManyField(to='goals.Interest'),
            preserve_default=True,
        ),
    ]
