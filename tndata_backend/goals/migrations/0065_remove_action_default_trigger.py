# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0064_create_single_action_triggers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='default_trigger',
        ),
    ]
