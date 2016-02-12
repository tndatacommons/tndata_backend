# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0018_gcmmessage_queue_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gcmmessage',
            options={'verbose_name': 'GCM Message', 'verbose_name_plural': 'GCM Messages', 'ordering': ['-success', 'deliver_on', 'priority', '-created_on']},
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='priority',
            field=models.CharField(choices=[('low', 'Low Priority'), ('medium', 'Medium Priority'), ('high', 'High Priority')], max_length=32, db_index=True, default='low'),
        ),
    ]
