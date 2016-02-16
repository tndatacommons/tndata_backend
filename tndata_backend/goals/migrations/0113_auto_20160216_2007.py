# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0112_auto_20160120_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customaction',
            name='custom_trigger',
            field=models.ForeignKey(to='goals.Trigger', null=True, blank=True),
        ),
    ]
