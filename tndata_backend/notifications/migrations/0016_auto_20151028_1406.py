# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0015_remove_gcmmessages'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='gcmmessage',
            unique_together=set([('user', 'title', 'message', 'deliver_on')]),
        ),
    ]
