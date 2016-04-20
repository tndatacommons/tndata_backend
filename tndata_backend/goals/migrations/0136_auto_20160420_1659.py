# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0135_category_selected_by_default'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='goal',
            options={'ordering': ['sequence_order', 'title'], 'verbose_name': 'Goal', 'permissions': (('view_goal', 'Can view Goals'), ('decline_goal', 'Can Decline Goals'), ('publish_goal', 'Can Publish Goals')), 'verbose_name_plural': 'Goals'},
        ),
        migrations.AddField(
            model_name='goal',
            name='sequence_order',
            field=models.IntegerField(default=0, db_index=True, blank=True, help_text='Optional ordering for a sequence of goals'),
        ),
    ]
