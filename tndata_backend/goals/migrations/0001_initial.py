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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, unique=True, db_index=True)),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('summary', models.TextField()),
                ('description', models.TextField()),
                ('default_reminder_time', models.TimeField(blank=True, null=True)),
                ('default_reminder_frequency', models.CharField(max_length=10, blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')])),
            ],
            options={
                'verbose_name_plural': 'Action',
                'verbose_name': 'Action',
                'ordering': ['order', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionTaken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_completed', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name_plural': 'Actions Taken',
                'verbose_name': 'Action Taken',
                'ordering': ['date_completed', 'selected_action', 'user'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, unique=True, db_index=True)),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Category',
                'verbose_name': 'Category',
                'ordering': ['order', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomReminder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField(blank=True, null=True)),
                ('frequency', models.CharField(max_length=10, blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')])),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Custom Reminders',
                'verbose_name': 'Custom Reminder',
                'ordering': ['action', 'user', 'time'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, unique=True, db_index=True)),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Interest',
                'verbose_name': 'Interest',
                'ordering': ['order', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterestGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('public', models.BooleanField(default=True)),
                ('category', models.ForeignKey(to='goals.Category')),
                ('interest', models.ManyToManyField(blank=True, to='goals.Interest', null=True)),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_selected', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Selected Actions',
                'verbose_name': 'Selected Action',
                'ordering': ['date_selected'],
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
