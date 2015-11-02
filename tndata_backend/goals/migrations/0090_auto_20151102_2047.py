# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0089_remove_trigger_location'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trigger',
            options={'permissions': (('view_trigger', 'Can view Triggers'), ('decline_trigger', 'Can Decline Triggers'), ('publish_trigger', 'Can Publish Triggers')), 'verbose_name': 'Trigger', 'verbose_name_plural': 'Triggers', 'ordering': ['name', 'id']},
        ),
        migrations.AlterField(
            model_name='trigger',
            name='name',
            field=models.CharField(max_length=128, help_text='A human-friendly name for this trigger', db_index=True),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='name_slug',
            field=models.SlugField(max_length=128),
        ),
    ]
