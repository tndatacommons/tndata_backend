# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0011_remove_gcmmessage_registrations_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='gcmmessage',
            name='registration_ids',
            field=models.TextField(blank=True, help_text='The registration_ids that GCM says it delivered to'),
        ),
    ]
