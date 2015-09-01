# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0009_auto_20150901_1659'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gcmmessage',
            options={'verbose_name_plural': 'GCM Messages', 'verbose_name': 'GCM Message', 'ordering': ['-success', 'deliver_on', '-created_on']},
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='registrations_ids',
            field=models.TextField(blank=True, help_text='The registration_ids that GCM says it delivered to'),
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='response_data',
            field=jsonfield.fields.JSONField(blank=True, default={}, help_text='The response data we get from GCM after it delivers this'),
        ),
    ]
