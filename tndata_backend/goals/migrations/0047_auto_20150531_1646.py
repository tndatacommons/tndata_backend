# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0046_behaviorprogress_goalprogress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behaviorprogress',
            name='status',
            field=models.IntegerField(choices=[(1, 'Off Course'), (2, 'Seeking'), (3, 'On Course')]),
        ),
    ]
