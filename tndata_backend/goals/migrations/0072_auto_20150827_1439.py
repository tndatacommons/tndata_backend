# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0071_packageenrollment_prevent_custom_triggers'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='consent_more',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='category',
            name='consent_summary',
            field=models.TextField(blank=True),
        ),
    ]
