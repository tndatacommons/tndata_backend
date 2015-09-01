# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0010_auto_20150901_2024'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gcmmessage',
            name='registrations_ids',
        ),
    ]
