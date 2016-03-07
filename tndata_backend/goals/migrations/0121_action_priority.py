# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0120_auto_20160303_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='priority',
            field=models.PositiveIntegerField(choices=[(3, 'Default'), (2, 'Medium'), (1, 'High')], help_text='Priority determine how notifications get queued for delivery', default=3),
        ),
    ]
