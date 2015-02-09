# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0003_auto_20150121_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='default_reminder_frequency',
            field=models.CharField(choices=[('never', 'Never'), ('daily', 'Every Day'), ('weekly', 'Every Week'), ('monthly', 'Every Month'), ('yearly', 'Every Year')], help_text='Choose a default frequency for the reminders.', max_length=10, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='default_reminder_time',
            field=models.TimeField(blank=True, help_text='Enter a time in 24-hour format, e.g. 13:30 for 1:30pm', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='description',
            field=models.TextField(verbose_name='Behavior', help_text='The full text of this behavior.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='icon',
            field=models.ImageField(blank=True, help_text='Upload an image to be displayed for this Action.', upload_to='goals/action', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='interests',
            field=models.ManyToManyField(to='goals.Interest', help_text='Select the Interests under which to display this Action.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='name',
            field=models.CharField(verbose_name='Title', db_index=True, help_text='A one-line title for this Action.', unique=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='order',
            field=models.PositiveIntegerField(help_text='Controls the order in which Categories are displayed.', unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='summary',
            field=models.TextField(verbose_name='Intro Text', help_text='A short bit of introductory text that will be displayed before the action is selected.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='description',
            field=models.TextField(help_text='Short description of this Category.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.ImageField(blank=True, help_text='Upload an image to be displayed next to the Category.', upload_to='goals/category', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(verbose_name='Title', db_index=True, help_text='A Title for the Category.', unique=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='order',
            field=models.PositiveIntegerField(help_text='Controls the order in which Categories are displayed.', unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='description',
            field=models.TextField(help_text='Short description of this Interest.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='name',
            field=models.CharField(verbose_name='Title', db_index=True, help_text='A one-line title for this Interest.', unique=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='notes',
            field=models.TextField(blank=True, help_text='Additional notes regarding this Interest.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interest',
            name='order',
            field=models.PositiveIntegerField(help_text='Controls the order in which Interests are displayed.', unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interestgroup',
            name='category',
            field=models.ForeignKey(to='goals.Category', help_text='The Category under which this group appears.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interestgroup',
            name='interests',
            field=models.ManyToManyField(to='goals.Interest', blank=True, help_text='Select the Interests to group together.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='interestgroup',
            name='name',
            field=models.CharField(verbose_name='Title', db_index=True, help_text='Give this group a one-line title.', unique=True, max_length=128),
            preserve_default=True,
        ),
    ]
