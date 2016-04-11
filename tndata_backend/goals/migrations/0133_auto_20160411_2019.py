# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0132_update_point_of_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='behavior',
            name='action_buckets_checkup',
            field=models.IntegerField(help_text='The number of CHECKUP actions in this behavior.', default=0, blank=True),
        ),
        migrations.AddField(
            model_name='behavior',
            name='action_buckets_core',
            field=models.IntegerField(help_text='The number of CORE actions in this behavior.', default=0, blank=True),
        ),
        migrations.AddField(
            model_name='behavior',
            name='action_buckets_helper',
            field=models.IntegerField(help_text='The number of HELPER actions in this behavior.', default=0, blank=True),
        ),
        migrations.AddField(
            model_name='behavior',
            name='action_buckets_prep',
            field=models.IntegerField(help_text='The number of PREP actions in this behavior.', default=0, blank=True),
        ),
    ]
