# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0038_remove_behavior_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='description',
            field=models.TextField(help_text='A brief (250 characters) description about this item.', blank=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='notification_text',
            field=models.CharField(help_text='Text of the notification (50 characters)', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='title',
            field=models.CharField(db_index=True, unique=True, max_length=256, help_text='A unique title for this item (50 characters)'),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='description',
            field=models.TextField(help_text='A brief (250 characters) description about this item.', blank=True),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='informal_list',
            field=models.TextField(help_text='Use this section to create a list of specific actions for this behavior. This list will be reproduced as a mnemonic on the Action entry page', blank=True),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='notification_text',
            field=models.CharField(help_text='Text of the notification (50 characters)', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='title',
            field=models.CharField(db_index=True, unique=True, max_length=256, help_text='A unique title for this item (50 characters)'),
        ),
        migrations.AlterField(
            model_name='category',
            name='description',
            field=models.TextField(help_text='A short (250 character) description for this Category'),
        ),
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.CharField(db_index=True, unique=True, max_length=128, help_text='A Title for the Category (50 characters)'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='description',
            field=models.TextField(help_text='A short (250 character) description for this Goal', blank=True),
        ),
        migrations.AlterField(
            model_name='goal',
            name='icon',
            field=models.ImageField(null=True, upload_to='goals/goal', help_text='Upload an icon (256x256) for this goal', blank=True),
        ),
        migrations.AlterField(
            model_name='goal',
            name='title',
            field=models.CharField(db_index=True, unique=True, max_length=256, help_text='A Title for the Goal (50 characters)'),
        ),
    ]
