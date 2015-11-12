# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0093_auto_20151109_1952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercompletedaction',
            name='state',
            field=models.CharField(max_length=32, choices=[('uncompleted', 'Uncompleted'), ('completed', 'Completed'), ('dismissed', 'Dismissed'), ('snoozed', 'Snoozed')], default='-'),
        ),
    ]
