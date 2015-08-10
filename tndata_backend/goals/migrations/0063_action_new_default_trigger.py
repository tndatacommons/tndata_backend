# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0062_auto_20150805_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='new_default_trigger',
            field=models.OneToOneField(help_text='A trigger/reminder for this behavior', related_name='action_default', null=True, blank=True, to='goals.Trigger'),
        ),
    ]
