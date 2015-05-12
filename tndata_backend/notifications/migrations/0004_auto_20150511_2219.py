# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_auto_20150511_2203'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='gcmmessage',
            unique_together=set([('user', 'message_id')]),
        ),
        migrations.RemoveField(
            model_name='gcmmessage',
            name='registration_id',
        ),
    ]
