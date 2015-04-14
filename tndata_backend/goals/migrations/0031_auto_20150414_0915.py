# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0030_auto_20150413_1724'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'verbose_name_plural': 'Actions', 'permissions': (('view_action', 'Can view Actions'), ('decline_action', 'Can Decline Actions'), ('publish_action', 'Can Publish Actions')), 'verbose_name': 'Action'},
        ),
        migrations.AlterModelOptions(
            name='behavior',
            options={'verbose_name_plural': 'Behaviors', 'permissions': (('view_behavior', 'Can view Permissions'), ('decline_behavior', 'Can Decline Permissions'), ('publish_behavior', 'Can Publish Permissions')), 'verbose_name': 'Behavior'},
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'Categories', 'permissions': (('view_category', 'Can view Categories'), ('decline_category', 'Can Decline Categories'), ('publish_category', 'Can Publish Categories')), 'ordering': ['order', 'title'], 'verbose_name': 'Category'},
        ),
        migrations.AlterModelOptions(
            name='goal',
            options={'verbose_name_plural': 'Goals', 'permissions': (('view_goal', 'Can view Goals'), ('decline_goal', 'Can Decline Goals'), ('publish_goal', 'Can Publish Goals')), 'verbose_name': 'Goal'},
        ),
        migrations.AlterModelOptions(
            name='trigger',
            options={'verbose_name_plural': 'Triggers', 'permissions': (('view_trigger', 'Can view Triggers'), ('decline_trigger', 'Can Decline Triggers'), ('publish_trigger', 'Can Publish Triggers')), 'verbose_name': 'Trigger'},
        ),
    ]
