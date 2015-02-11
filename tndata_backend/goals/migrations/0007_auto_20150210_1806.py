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
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(db_index=True, help_text='Unique, informal and internal. Conversational identifier only.', unique=True, max_length=128)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('notes', models.TextField(help_text='Misc nodes about this behavior', blank=True)),
                ('source_notes', models.TextField(help_text='Narrative notes about the source', blank=True)),
                ('source_link', models.URLField(null=True, blank=True, help_text='A link to the source.', max_length=256)),
                ('title', models.CharField(db_index=True, help_text='Unique, Formal title. Displayed as a caption in the app.', unique=True, max_length=256)),
                ('description', models.TextField(help_text='Brief description.', blank=True)),
                ('case', models.TextField(help_text='Brief description of why this is useful.', blank=True)),
                ('outcome', models.TextField(help_text='Brief description of what the user can expect to get by adopting the behavior', blank=True)),
                ('narrative_block', models.TextField(help_text='Persuasive narrative description, case, outcome of the behavior', blank=True)),
                ('external_resource', models.CharField(help_text='A link or reference to an outside resource necessary for adoption', blank=True, max_length=256)),
                ('notification_text', models.CharField(help_text='Text message delivered through notification channel', blank=True, max_length=256)),
                ('icon', models.ImageField(null=True, blank=True, upload_to=goals.models._behavior_icon_path, help_text='A Small icon for the Action.')),
                ('image', models.ImageField(null=True, blank=True, upload_to=goals.models._behavior_img_path, help_text='Upload an image to be displayed for the Behavior Action.')),
                ('sequence_order', models.IntegerField(help_text='Order/number of action in stepwise behavior sequence', default=0, db_index=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Behavior Action',
                'verbose_name_plural': 'Behavior Actions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BehaviorSequence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('informal_list', models.TextField(help_text='Working list of the behavior sequence. Mnemonic only.', blank=True)),
                ('categories', models.ManyToManyField(null=True, blank=True, to='goals.Category', help_text='Select the Categories in which this should appear.')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Behavior Sequence',
                'verbose_name_plural': 'Behavior Sequences',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(db_index=True, help_text='An Internal name for this goal.', unique=True, max_length=128)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('title', models.CharField(db_index=True, help_text='A public Title for this goal.', unique=True, max_length=256)),
                ('description', models.TextField(help_text='Short description of this Category.', blank=True)),
                ('outcome', models.TextField(help_text='Desired outcome of this Goal.', blank=True)),
                ('categories', models.ManyToManyField(null=True, blank=True, to='goals.Category', help_text='Select the Categories in which this Goal should appear.')),
                ('interests', models.ManyToManyField(null=True, blank=True, to='goals.Interest', help_text='Select the Interests in which this Goal should be organized.')),
            ],
            options={
                'verbose_name': 'Goal',
                'verbose_name_plural': 'Goals',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Trigger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(db_index=True, help_text='Give this trigger a helpful name. It must be unique, and will be used in drop-down lists and other places where youcan select it later.', unique=True, max_length=128)),
                ('name_slug', models.SlugField(unique=True, max_length=128)),
                ('trigger_type', models.CharField(choices=[('time', 'Time'), ('place', 'Place')], help_text='The type of Trigger used, e.g. Time, Place, etc', blank=True, max_length=10)),
                ('frequency', models.CharField(choices=[('one-time', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], help_text='How frequently a trigger is fired', blank=True, max_length=10)),
                ('time', models.TimeField(null=True, blank=True, help_text='Time the trigger/notification will fire, in 24-hour format.')),
                ('date', models.DateField(null=True, blank=True, help_text='The date of the trigger/notification. If the trigger is recurring, notifications will start on this date.')),
                ('location', models.CharField(help_text="Only used when Trigger type is location. Can be 'home', 'work', or a (lat, long) pair.", blank=True, max_length=256)),
                ('text', models.CharField(help_text='The Trigger text shown to the user.', blank=True, max_length='140')),
                ('instruction', models.TextField(help_text='Instructions sent to the user.', blank=True)),
            ],
            options={
                'verbose_name': 'Trigger',
                'verbose_name_plural': 'Triggers',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='behaviorsequence',
            name='goals',
            field=models.ManyToManyField(null=True, blank=True, to='goals.Goal', help_text='Select the Goal(s) that this Behavior achieves.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behaviorsequence',
            name='interests',
            field=models.ManyToManyField(null=True, blank=True, to='goals.Interest', help_text='Select the Interest(s) under which this should be organized.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavioraction',
            name='default_trigger',
            field=models.ForeignKey(null=True, blank=True, help_text='A trigger/reminder for this behavior', to='goals.Trigger'),
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
            field=models.CharField(help_text='Formal title, used publicly.', blank=True, default='', max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='description',
            field=models.TextField(help_text='Short description of this Interest.', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='name',
            field=models.CharField(db_index=True, help_text='An informal/internal name. Conversational identifier only.', unique=True, max_length=128),
            preserve_default=True,
        ),
    ]
