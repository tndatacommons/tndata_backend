# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0006_auto_20150512_1027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gcmmessage',
            name='deliver_on',
            field=models.DateTimeField(db_index=True, help_text='Date/Time on which the message should be delivered (UTC)'),
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='expire_on',
            field=models.DateTimeField(null=True, help_text='Date/Time when this should expire (UTC)', blank=True),
        ),
    ]
