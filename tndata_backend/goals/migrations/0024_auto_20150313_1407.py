# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0023_rename_models_behaviorsequence_and_behavioraction'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'verbose_name_plural': 'Actions', 'verbose_name': 'Action'},
        ),
        migrations.AlterModelOptions(
            name='behavior',
            options={'verbose_name_plural': 'Behaviors', 'verbose_name': 'Behavior'},
        ),
        migrations.AlterField(
            model_name='behavior',
            name='informal_list',
            field=models.TextField(help_text='A working list of actions associated with the behavior. Mnemonic only.', blank=True),
            preserve_default=True,
        ),
    ]
