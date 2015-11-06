# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import goals.models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0091_auto_20151106_2115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.ImageField(null=True, help_text='Upload a square icon to be displayed for the Category.', upload_to=goals.models._category_icon_path, blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.ImageField(null=True, help_text='A Hero image to be displayed at the top of the Category pager', upload_to=goals.models._catetgory_image_path, blank=True),
        ),
        migrations.AlterField(
            model_name='goal',
            name='icon',
            field=models.ImageField(null=True, help_text='Upload an icon (256x256) for this goal', upload_to=goals.models._goal_icon_path, blank=True),
        ),
    ]
