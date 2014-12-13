# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behaviorstep',
            name='default_time',
            field=models.TimeField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='behaviorstep',
            name='reminder_type',
            field=models.CharField(blank=True, choices=[('temporal', 'Temporal'), ('geolocation', 'Geolocation')], max_length=32),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customreminder',
            name='reminder_type',
            field=models.CharField(blank=True, choices=[('temporal', 'Temporal'), ('geolocation', 'Geolocation')], max_length=32),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customreminder',
            name='time',
            field=models.TimeField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
