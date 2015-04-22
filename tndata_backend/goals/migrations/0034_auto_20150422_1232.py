# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0033_create_content_editor_and_author_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behavior',
            name='categories',
            field=models.ManyToManyField(help_text='Select the Categories in which this should appear.', blank=True, to='goals.Category'),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='goals',
            field=models.ManyToManyField(help_text='Select the Goal(s) that this Behavior achieves.', blank=True, to='goals.Goal'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='categories',
            field=models.ManyToManyField(help_text='Select the Categories in which this Goal should appear.', blank=True, to='goals.Category'),
        ),
    ]
