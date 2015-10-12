# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0084_useraction_prev_trigger_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usercompletedaction',
            options={'ordering': ['-updated_on', 'user', 'action'], 'verbose_name_plural': 'User Completed Action', 'verbose_name': 'User Completed Action'},
        ),
        migrations.AlterField(
            model_name='usercompletedaction',
            name='state',
            field=models.CharField(default='-', choices=[('completed', 'Completed'), ('dismissed', 'Dismissed'), ('snoozed', 'Snoozed')], max_length=32),
        ),
    ]
