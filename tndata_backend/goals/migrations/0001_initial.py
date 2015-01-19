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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True)),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('summary', models.TextField()),
                ('description', models.TextField()),
                ('default_reminder_time', models.TimeField(null=True, blank=True)),
                ('default_reminder_frequency', models.CharField(max_length=10, blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')])),
            ],
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'Action',
                'verbose_name_plural': 'Action',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionTaken',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('date_completed', models.DateTimeField(db_index=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['date_completed', 'selected_action', 'user'],
                'verbose_name': 'Action Taken',
                'verbose_name_plural': 'Actions Taken',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True)),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'Category',
                'verbose_name_plural': 'Category',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomReminder',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('time', models.TimeField(null=True, blank=True)),
                ('frequency', models.CharField(max_length=10, blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')])),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['action', 'user', 'time'],
                'verbose_name': 'Custom Reminder',
                'verbose_name_plural': 'Custom Reminders',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True)),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'Interest',
                'verbose_name_plural': 'Interest',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterestGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('public', models.BooleanField(default=True)),
                ('category', models.ForeignKey(to='goals.Category')),
                ('interest', models.ForeignKey(to='goals.Interest')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedAction',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('date_selected', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['date_selected'],
                'verbose_name': 'Selected Action',
                'verbose_name_plural': 'Selected Actions',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='interest',
            name='categories',
            field=models.ManyToManyField(through='goals.InterestGroup', to='goals.Category'),
            preserve_default=True,
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
