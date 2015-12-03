# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0097_auto_20151125_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='start_when_selected',
            field=models.BooleanField(default=False, help_text='Should this trigger start on the day the user selects the action? '),
        ),
    ]
