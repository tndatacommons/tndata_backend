# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0095_auto_20151119_2222'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='stop_on_complete',
            field=models.BooleanField(help_text='Should reminders stop after the action has been completed?', default=False),
        ),
    ]
