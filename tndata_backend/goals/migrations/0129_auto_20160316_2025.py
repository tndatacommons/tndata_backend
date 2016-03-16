# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0128_auto_20160315_2015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='bucket',
            field=models.CharField(max_length=32, default='core', help_text='The "bucket" from which this object is selected when queueing up notifications.', choices=[('prep', 'Preparatory'), ('core', 'Core'), ('helper', 'Helper'), ('checkup', 'Checkup')], blank=True),
        ),
    ]
