# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0053_auto_20150702_0729'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='action_type',
            field=models.CharField(max_length='32', default='custom', db_index=True, choices=[('starter', 'Starter Step'), ('tiny', 'Tiny Version'), ('resource', 'Resource'), ('now', 'Right Now'), ('custom', 'Custom')]),
        ),
        migrations.AlterField(
            model_name='action',
            name='external_resource',
            field=models.CharField(max_length=256, blank=True, help_text='An external resource is something that will help a user accomplish a task. It could be a phone number, link to a website, link to another app, or GPS coordinates. '),
        ),
        migrations.AlterField(
            model_name='behavior',
            name='external_resource',
            field=models.CharField(max_length=256, blank=True, help_text='An external resource is something that will help a user accomplish a task. It could be a phone number, link to a website, link to another app, or GPS coordinates. '),
        ),
    ]
