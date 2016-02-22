# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0113_auto_20160216_2007'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trigger',
            options={'verbose_name': 'Trigger', 'permissions': (('view_trigger', 'Can view Triggers'), ('decline_trigger', 'Can Decline Triggers'), ('publish_trigger', 'Can Publish Triggers')), 'verbose_name_plural': 'Triggers', 'ordering': ['disabled', 'name', 'id']},
        ),
        migrations.AddField(
            model_name='trigger',
            name='disabled',
            field=models.BooleanField(default=False, help_text='When disabled, a Trigger will stop generating new events.', db_index=True),
        ),
    ]
