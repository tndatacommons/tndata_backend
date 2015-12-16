# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0098_trigger_start_when_selected'),
    ]

    operations = [
        migrations.AddField(
            model_name='behavior',
            name='sequence_order',
            field=models.IntegerField(db_index=True, blank=True, default=0, help_text='Optional ordering for a sequence of behaviors'),
        ),
    ]
