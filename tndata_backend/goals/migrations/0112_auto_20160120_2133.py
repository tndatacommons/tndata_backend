# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0111_auto_20160120_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='primary_category',
            field=models.ForeignKey(blank=True, help_text='A primary category associated with this action. Typically this is the parent category of the primaary goal.', null=True, to='goals.Category'),
        ),
        migrations.AddField(
            model_name='usergoal',
            name='primary_category',
            field=models.ForeignKey(blank=True, help_text='A primary category associated with the Goal. Typically this is the Category through which the goal was selected.', null=True, to='goals.Category'),
        ),
    ]
