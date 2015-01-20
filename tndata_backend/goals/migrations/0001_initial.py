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
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('summary', models.TextField()),
                ('description', models.TextField()),
                ('default_reminder_time', models.TimeField(blank=True, null=True)),
                ('default_reminder_frequency', models.CharField(blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], max_length=10)),
            ],
            options={
                'verbose_name': 'Action',
                'verbose_name_plural': 'Action',
                'ordering': ['order', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionTaken',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('date_completed', models.DateTimeField(db_index=True, auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Action Taken',
                'verbose_name_plural': 'Actions Taken',
                'ordering': ['date_completed', 'selected_action', 'user'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Category',
                'ordering': ['order', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomReminder',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('time', models.TimeField(blank=True, null=True)),
                ('frequency', models.CharField(blank=True, choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], max_length=10)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Custom Reminder',
                'verbose_name_plural': 'Custom Reminders',
                'ordering': ['action', 'user', 'time'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name': 'Interest',
                'verbose_name_plural': 'Interest',
                'ordering': ['order', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterestGroup',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=128)),
                ('public', models.BooleanField(default=True)),
                ('category', models.ForeignKey(to='goals.Category')),
                ('interests', models.ManyToManyField(blank=True, to='goals.Interest', null=True)),
            ],
            options={
                'verbose_name': 'Interest Group',
                'verbose_name_plural': 'Interest Groups',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedAction',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('date_selected', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Selected Action',
                'verbose_name_plural': 'Selected Actions',
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
