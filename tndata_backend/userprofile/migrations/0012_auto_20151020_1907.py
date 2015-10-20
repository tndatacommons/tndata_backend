# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0011_create_places'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='needs_onboarding',
            field=models.BooleanField(default=True),
        ),
    ]
