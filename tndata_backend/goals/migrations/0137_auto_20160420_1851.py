# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0136_auto_20160420_1659'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'permissions': (('view_action', 'Can view Actions'), ('decline_action', 'Can Decline Actions'), ('publish_action', 'Can Publish Actions')), 'verbose_name_plural': 'Actions', 'verbose_name': 'Action', 'ordering': ['sequence_order', 'action_type', 'title']},
        ),
    ]
