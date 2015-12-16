# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0099_behavior_sequence_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='behavior',
            options={'ordering': ['sequence_order', 'title'], 'permissions': (('view_behavior', 'Can view Permissions'), ('decline_behavior', 'Can Decline Permissions'), ('publish_behavior', 'Can Publish Permissions')), 'verbose_name': 'Behavior', 'verbose_name_plural': 'Behaviors'},
        ),
    ]
