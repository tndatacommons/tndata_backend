# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0049_trigger_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='custom_trigger',
            field=models.ForeignKey(blank=True, to='goals.Trigger', help_text='A User-defined trigger for this behavior', null=True),
        ),
        migrations.AddField(
            model_name='userbehavior',
            name='custom_trigger',
            field=models.ForeignKey(blank=True, to='goals.Trigger', help_text='A User-defined trigger for this behavior', null=True),
        ),
    ]
