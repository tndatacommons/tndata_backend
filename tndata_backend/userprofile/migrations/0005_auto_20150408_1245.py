# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0004_auto_20150408_1245'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='marital_status',
            new_name='relationship_status',
        ),
    ]
