# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='action',
            old_name='default_reminder_frequencey',
            new_name='default_reminder_frequency',
        ),
    ]
