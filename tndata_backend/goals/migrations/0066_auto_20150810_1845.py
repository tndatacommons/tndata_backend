# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0065_remove_action_default_trigger'),
    ]

    operations = [
        migrations.RenameField(
            model_name='action',
            old_name='new_default_trigger',
            new_name='default_trigger',
        ),
    ]
