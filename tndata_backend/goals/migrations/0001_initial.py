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
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, db_index=True)),
                ('summary', models.TextField()),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ['goal', 'name'],
                'verbose_name': 'Behavior',
                'verbose_name_plural': 'Behaviors',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BehaviorStep',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, db_index=True)),
                ('description', models.TextField()),
                ('reminder_type', models.CharField(max_length=32, choices=[('temporal', 'Temporal'), ('geolocation', 'Geolocation')], blank=True)),
                ('default_time', models.TimeField(null=True, blank=True)),
                ('default_repeat', models.CharField(max_length=32, choices=[('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], blank=True)),
                ('default_location', models.CharField(max_length=32, blank=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Behavior Step',
                'verbose_name_plural': 'Behavior Steps',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChosenBehavior',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('date_selected', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
            ],
            options={
                'ordering': ['date_selected'],
                'verbose_name': 'Chosen Behavior',
                'verbose_name_plural': 'Chosen Behaviors',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompletedBehaviorStep',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('date_completed', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('behavior', models.ForeignKey(to='goals.Behavior')),
                ('behavior_step', models.ForeignKey(to='goals.BehaviorStep')),
            ],
            options={
                'ordering': ['date_completed'],
                'verbose_name': 'Chosen Behavior Step',
                'verbose_name_plural': 'Chosen Behavior Steps',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomReminder',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(max_length=32, choices=[('temporal', 'Temporal'), ('geolocation', 'Geolocation')], blank=True)),
                ('time', models.TimeField(null=True, blank=True)),
                ('repeat', models.CharField(max_length=32, choices=[('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], blank=True)),
                ('location', models.CharField(max_length=32, blank=True)),
                ('behavior_step', models.ForeignKey(to='goals.BehaviorStep')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['behavior_step'],
                'verbose_name': 'Custom Reminder',
                'verbose_name_plural': 'Custom Reminders',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=128, db_index=True)),
                ('explanation', models.TextField()),
                ('max_neef_tags', models.TextField()),
                ('sdt_major', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['rank', 'name'],
                'verbose_name': 'Goal',
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
