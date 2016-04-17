# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0019_auto_20160405_1734'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='ip_address',
            field=models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True),
        ),
    ]
