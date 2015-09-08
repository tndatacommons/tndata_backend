# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0009_auto_20150908_1727'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userplace',
            unique_together=set([('user', 'place')]),
        ),
    ]
