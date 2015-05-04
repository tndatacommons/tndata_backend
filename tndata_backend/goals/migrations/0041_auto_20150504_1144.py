# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0040_swap_description_narrative_block'),
    ]

    operations = [
        migrations.RenameField(
            model_name='action',
            old_name='narrative_block',
            new_name='more_info',
        ),
        migrations.RenameField(
            model_name='behavior',
            old_name='narrative_block',
            new_name='more_info',
        ),
    ]
