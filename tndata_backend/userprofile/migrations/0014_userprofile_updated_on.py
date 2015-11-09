# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0013_auto_20151109_1811'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
