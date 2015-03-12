# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import goals.models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0021_auto_20150312_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behavioraction',
            name='description',
            field=models.TextField(blank=True, help_text='A brief description about this item.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to=goals.models._behavior_icon_path, help_text='A square icon for this item in the app, preferrably 512x512.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=goals.models._behavior_img_path, help_text='An image to be displayed for this item, preferrably 1024x1024.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='narrative_block',
            field=models.TextField(blank=True, help_text='Persuasive narrative description: Tell the user why this is imporrtant.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='notes',
            field=models.TextField(blank=True, help_text='Misc notes about this item. This is for your use and will not be displayed in the app.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='sequence',
            field=models.ForeignKey(verbose_name='behavior', to='goals.BehaviorSequence'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='sequence_order',
            field=models.IntegerField(db_index=True, help_text='Order/number of action in stepwise sequence of behaviors', default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='source_notes',
            field=models.TextField(blank=True, help_text='Narrative notes about the source of this item.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behavioraction',
            name='title',
            field=models.CharField(db_index=True, max_length=256, help_text='A unique title for this item. This will be displayed in the app.', unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='description',
            field=models.TextField(blank=True, help_text='A brief description about this item.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to=goals.models._behavior_icon_path, help_text='A square icon for this item in the app, preferrably 512x512.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=goals.models._behavior_img_path, help_text='An image to be displayed for this item, preferrably 1024x1024.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='narrative_block',
            field=models.TextField(blank=True, help_text='Persuasive narrative description: Tell the user why this is imporrtant.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='notes',
            field=models.TextField(blank=True, help_text='Misc notes about this item. This is for your use and will not be displayed in the app.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='source_notes',
            field=models.TextField(blank=True, help_text='Narrative notes about the source of this item.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorsequence',
            name='title',
            field=models.CharField(db_index=True, max_length=256, help_text='A unique title for this item. This will be displayed in the app.', unique=True),
            preserve_default=True,
        ),
    ]
