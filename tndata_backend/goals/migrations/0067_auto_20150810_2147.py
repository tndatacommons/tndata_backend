# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0066_auto_20150810_1845'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'verbose_name': 'Action', 'ordering': ['sequence_order', 'title'], 'permissions': (('view_action', 'Can view Actions'), ('decline_action', 'Can Decline Actions'), ('publish_action', 'Can Publish Actions')), 'verbose_name_plural': 'Actions'},
        ),
        migrations.AlterModelOptions(
            name='behavior',
            options={'verbose_name': 'Behavior', 'ordering': ['title'], 'permissions': (('view_behavior', 'Can view Permissions'), ('decline_behavior', 'Can Decline Permissions'), ('publish_behavior', 'Can Publish Permissions')), 'verbose_name_plural': 'Behaviors'},
        ),
        migrations.AlterModelOptions(
            name='goal',
            options={'verbose_name': 'Goal', 'ordering': ['title'], 'permissions': (('view_goal', 'Can view Goals'), ('decline_goal', 'Can Decline Goals'), ('publish_goal', 'Can Publish Goals')), 'verbose_name_plural': 'Goals'},
        ),
    ]
