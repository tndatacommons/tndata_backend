# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0126_convert_core_actions_to_showing'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usercompletedaction',
            options={'verbose_name': 'User Completed Action', 'get_latest_by': 'updated_on', 'ordering': ['-updated_on', 'user', 'action'], 'verbose_name_plural': 'User Completed Action'},
        ),
        migrations.AlterField(
            model_name='dailyprogress',
            name='behaviors_status',
            field=jsonfield.fields.JSONField(default=dict, blank=True, help_text="Describes the user's status on work toward this behavior; i.e. From which bucket should Actions be delivered."),
        ),
    ]
