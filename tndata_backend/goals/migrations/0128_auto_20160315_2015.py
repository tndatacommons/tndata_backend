# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0127_auto_20160310_2145'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'permissions': (('view_action', 'Can view Actions'), ('decline_action', 'Can Decline Actions'), ('publish_action', 'Can Publish Actions')), 'ordering': ['bucket', 'sequence_order', 'action_type', 'title'], 'verbose_name_plural': 'Actions', 'verbose_name': 'Action'},
        ),
    ]
