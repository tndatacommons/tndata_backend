# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('notifications', '0004_auto_20150511_2219'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gcmmessage',
            name='content',
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='message',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gcmmessage',
            name='title',
            field=models.CharField(default='', max_length=50),
        ),
    ]
