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
            name='Behavior',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=128)),
                ('summary', models.TextField()),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name': 'Behavior',
                'ordering': ['goal', 'name'],
                'verbose_name_plural': 'Behaviors',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BehaviorStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=128)),
                ('description', models.TextField()),
                ('reminder_type', models.CharField(choices=[('temporal', 'Temporal'), ('geolocation', 'Geolocation')], max_length=32)),
                ('default_time', models.DateTimeField(blank=True)),
                ('default_repeat', models.CharField(choices=[('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], max_length=32, blank=True)),
                ('default_location', models.CharField(max_length=32, blank=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
            ],
            options={
                'verbose_name': 'Behavior Step',
                'ordering': ['name'],
                'verbose_name_plural': 'Behavior Steps',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChosenBehavior',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('date_selected', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
            ],
            options={
                'verbose_name': 'Chosen Behavior',
                'ordering': ['date_selected'],
                'verbose_name_plural': 'Chosen Behaviors',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompletedBehaviorStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('date_completed', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
                ('behavior_step', models.ForeignKey(to='goals.BehaviorStep')),
            ],
            options={
                'verbose_name': 'Chosen Behavior Step',
                'ordering': ['date_completed'],
                'verbose_name_plural': 'Chosen Behavior Steps',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomReminder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('reminder_type', models.CharField(choices=[('temporal', 'Temporal'), ('geolocation', 'Geolocation')], max_length=32)),
                ('time', models.DateTimeField(blank=True)),
                ('repeat', models.CharField(choices=[('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], max_length=32, blank=True)),
                ('location', models.CharField(max_length=32, blank=True)),
                ('behavior_step', models.ForeignKey(to='goals.BehaviorStep')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Custom Reminder',
                'ordering': ['behavior_step'],
                'verbose_name_plural': 'Custom Reminders',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('rank', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(db_index=True, max_length=128)),
                ('explanation', models.TextField()),
                ('max_neef_tags', models.TextField()),
                ('sdt_major', models.CharField(max_length=128)),
            ],
            options={
                'verbose_name': 'Goal',
                'ordering': ['rank', 'name'],
                'verbose_name_plural': 'Goals',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='customreminder',
            unique_together=set([('user', 'behavior_step')]),
        ),
        migrations.AddField(
            model_name='completedbehaviorstep',
            name='goal',
            field=models.ForeignKey(to='goals.Goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='completedbehaviorstep',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chosenbehavior',
            name='goal',
            field=models.ForeignKey(to='goals.Goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chosenbehavior',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behaviorstep',
            name='goal',
            field=models.ForeignKey(to='goals.Goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavior',
            name='goal',
            field=models.ForeignKey(to='goals.Goal'),
            preserve_default=True,
        ),
    ]
