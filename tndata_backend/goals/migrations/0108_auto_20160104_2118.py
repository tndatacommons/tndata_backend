# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0107_auto_20160104_1636'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomAction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(db_index=True, max_length=128)),
                ('title_slug', models.SlugField(max_length=128)),
                ('notification_text', models.CharField(max_length=256)),
                ('next_trigger_date', models.DateTimeField(null=True, blank=True, editable=False)),
                ('prev_trigger_date', models.DateTimeField(null=True, blank=True, editable=False)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('custom_trigger', models.ForeignKey(null=True, blank=True, to='goals.Trigger')),
            ],
            options={
                'verbose_name_plural': 'Custom Actions',
                'verbose_name': 'Custom Action',
                'ordering': ['-created_on', 'title'],
            },
        ),
        migrations.CreateModel(
            name='CustomActionFeedback',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('text', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('customaction', models.ForeignKey(to='goals.CustomAction')),
            ],
            options={
                'verbose_name_plural': 'Custom Action Feedback',
                'verbose_name': 'Custom Action Feedback',
                'ordering': ['-created_on', 'user'],
            },
        ),
        migrations.CreateModel(
            name='CustomGoal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(db_index=True, max_length=128)),
                ('title_slug', models.SlugField(max_length=128)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Custom Goals',
                'verbose_name': 'Custom Goal',
                'ordering': ['-created_on', 'title'],
            },
        ),
        migrations.CreateModel(
            name='UserCompletedCustomAction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('state', models.CharField(choices=[('uncompleted', 'Uncompleted'), ('completed', 'Completed'), ('dismissed', 'Dismissed'), ('snoozed', 'Snoozed')], max_length=32, default='-')),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('customaction', models.ForeignKey(to='goals.CustomAction')),
                ('customgoal', models.ForeignKey(to='goals.CustomGoal')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Completed Custom Actions',
                'verbose_name': 'User Completed Custom Action',
                'ordering': ['-updated_on', 'user', 'customaction'],
            },
        ),
        migrations.AddField(
            model_name='customactionfeedback',
            name='customgoal',
            field=models.ForeignKey(to='goals.CustomGoal'),
        ),
        migrations.AddField(
            model_name='customactionfeedback',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customaction',
            name='customgoal',
            field=models.ForeignKey(to='goals.CustomGoal'),
        ),
        migrations.AddField(
            model_name='customaction',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
