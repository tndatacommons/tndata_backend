# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import goals.models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0006_auto_20150209_1746'),
    ]

    operations = [
        migrations.CreateModel(
            name='BehaviorAction',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True, help_text='Unique, informal and internal. Conversational identifier only.')),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('notes', models.TextField(blank=True, help_text='Misc nodes about this behavior')),
                ('source_notes', models.TextField(blank=True, help_text='Narrative notes about the source')),
                ('source_link', models.URLField(max_length=256, blank=True, null=True, help_text='A link to the source.')),
                ('title', models.CharField(max_length=256, db_index=True, unique=True, help_text='Unique, Formal title. Displayed as a caption in the app.')),
                ('description', models.TextField(blank=True, help_text='Brief description.')),
                ('case', models.TextField(blank=True, help_text='Brief description of why this is useful.')),
                ('outcome', models.TextField(blank=True, help_text='Brief description of what the user can expect to get by adopting the behavior')),
                ('narrative_block', models.TextField(blank=True, help_text='Persuasive narrative description, case, outcome of the behavior')),
                ('external_resource', models.CharField(max_length=256, blank=True, help_text='A link or reference to an outside resource necessary for adoption')),
                ('notification_text', models.CharField(max_length=256, blank=True, help_text='Text message delivered through notification channel')),
                ('icon', models.ImageField(blank=True, upload_to=goals.models._behavior_icon_path, null=True, help_text='A Small icon for the Action.')),
                ('image', models.ImageField(blank=True, upload_to=goals.models._behavior_img_path, null=True, help_text='Upload an image to be displayed for the Behavior Action.')),
                ('sequence_order', models.IntegerField(default=0, db_index=True, help_text='Order/number of action in stepwise behavior sequence')),
            ],
            options={
                'verbose_name_plural': 'Behavior Actions',
                'verbose_name': 'Behavior Action',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BehaviorSequence',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True, help_text='Unique, informal and internal. Conversational identifier only.')),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('notes', models.TextField(blank=True, help_text='Misc nodes about this behavior')),
                ('source_notes', models.TextField(blank=True, help_text='Narrative notes about the source')),
                ('source_link', models.URLField(max_length=256, blank=True, null=True, help_text='A link to the source.')),
                ('title', models.CharField(max_length=256, db_index=True, unique=True, help_text='Unique, Formal title. Displayed as a caption in the app.')),
                ('description', models.TextField(blank=True, help_text='Brief description.')),
                ('case', models.TextField(blank=True, help_text='Brief description of why this is useful.')),
                ('outcome', models.TextField(blank=True, help_text='Brief description of what the user can expect to get by adopting the behavior')),
                ('narrative_block', models.TextField(blank=True, help_text='Persuasive narrative description, case, outcome of the behavior')),
                ('external_resource', models.CharField(max_length=256, blank=True, help_text='A link or reference to an outside resource necessary for adoption')),
                ('notification_text', models.CharField(max_length=256, blank=True, help_text='Text message delivered through notification channel')),
                ('icon', models.ImageField(blank=True, upload_to=goals.models._behavior_icon_path, null=True, help_text='A Small icon for the Action.')),
                ('image', models.ImageField(blank=True, upload_to=goals.models._behavior_img_path, null=True, help_text='Upload an image to be displayed for the Behavior Action.')),
                ('informal_list', models.TextField(blank=True, help_text='Working list of the behavior sequence. Mnemonic only.')),
                ('categories', models.ManyToManyField(blank=True, null=True, to='goals.Category', help_text='Select the Categories in which this should appear.')),
            ],
            options={
                'verbose_name_plural': 'Behavior Sequences',
                'verbose_name': 'Behavior Sequence',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True, help_text='An Internal name for this goal.')),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('title', models.CharField(max_length=256, db_index=True, unique=True, help_text='A public Title for this goal.')),
                ('description', models.TextField(blank=True, help_text='Short description of this Category.')),
                ('outcome', models.TextField(blank=True, help_text='Desired outcome of this Goal.')),
                ('categories', models.ManyToManyField(blank=True, null=True, to='goals.Category', help_text='Select the Categories in which this Goal should appear.')),
                ('interests', models.ManyToManyField(blank=True, null=True, to='goals.Interest', help_text='Select the Interests in which this Goal should be organized.')),
            ],
            options={
                'verbose_name_plural': 'Goals',
                'verbose_name': 'Goal',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Trigger',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=128, db_index=True, unique=True, help_text='Give this trigger a helpful name. It must be unique, and will be used in drop-down lists and other places where youcan select it later.')),
                ('name_slug', models.SlugField(max_length=128, unique=True)),
                ('trigger_type', models.CharField(max_length=10, choices=[('time', 'Time'), ('place', 'Place')], blank=True, help_text='The type of Trigger used, e.g. Time, Place, etc')),
                ('frequency', models.CharField(max_length=10, choices=[('one-time', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], blank=True, help_text='How frequently a trigger is fired')),
                ('time', models.TimeField(blank=True, null=True, help_text='Time the trigger/notification will fire, in 24-hour format.')),
                ('date', models.DateField(blank=True, null=True, help_text='The date of the trigger/notification. If the trigger is recurring, notifications will start on this date.')),
                ('location', models.CharField(max_length=256, blank=True, help_text="Only used when Trigger type is location. Can be 'home', 'work', or a (lat, long) pair.")),
                ('text', models.CharField(max_length='140', blank=True, help_text='The Trigger text shown to the user.')),
                ('instruction', models.TextField(blank=True, help_text='Instructions sent to the user.')),
            ],
            options={
                'verbose_name_plural': 'Triggers',
                'verbose_name': 'Trigger',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='behaviorsequence',
            name='default_trigger',
            field=models.ForeignKey(to='goals.Trigger', blank=True, help_text='A trigger/reminder for this behavior', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behaviorsequence',
            name='goals',
            field=models.ManyToManyField(blank=True, null=True, to='goals.Goal', help_text='Select the Goal(s) that this Behavior achieves.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behaviorsequence',
            name='interests',
            field=models.ManyToManyField(blank=True, null=True, to='goals.Interest', help_text='Select the Interest(s) under which this should be organized.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavioraction',
            name='default_trigger',
            field=models.ForeignKey(to='goals.Trigger', blank=True, help_text='A trigger/reminder for this behavior', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavioraction',
            name='sequence',
            field=models.ForeignKey(to='goals.BehaviorSequence'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interest',
            name='title',
            field=models.CharField(default='', help_text='Formal title, used publicly.', blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='description',
            field=models.TextField(blank=True, help_text='Short description of this Interest.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='name',
            field=models.CharField(max_length=128, db_index=True, unique=True, help_text='An informal/internal name. Conversational identifier only.'),
            preserve_default=True,
        ),
    ]
