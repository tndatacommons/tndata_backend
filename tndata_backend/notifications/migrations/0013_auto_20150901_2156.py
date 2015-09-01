# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0012_gcmmessage_registration_ids'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='gcmmessage',
            unique_together=set([('user', 'title', 'message', 'deliver_on', 'object_id', 'content_type')]),
        ),
        migrations.RemoveField(
            model_name='gcmmessage',
            name='message_id',
        ),
    ]
