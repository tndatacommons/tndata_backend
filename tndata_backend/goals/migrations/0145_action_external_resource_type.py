# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0144_auto_20160517_2104'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='external_resource_type',
            field=models.CharField(help_text='An internally-used field that makes it easier for client apps to determine how to handle the external_resource data.', max_length=32, choices=[('link', 'Link'), ('phone', 'Phone Number'), ('datetime', 'Date/Time')], blank=True),
        ),
    ]
