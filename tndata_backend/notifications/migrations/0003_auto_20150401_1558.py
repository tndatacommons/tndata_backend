# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_auto_20150401_1447'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gcmmessage',
            name='content',
            field=jsonfield.fields.JSONField(help_text='JSON content for the message'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='deliver_on',
            field=models.DateTimeField(help_text='Date/Time on which the message should be delivered', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='expire_on',
            field=models.DateTimeField(help_text='Date/Time on which this message should expire (be deleted)', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='message_id',
            field=models.CharField(max_length=32, help_text='Unique ID for this message.', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='registration_id',
            field=models.CharField(max_length=256, help_text='The Android device ID', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='success',
            field=models.NullBooleanField(help_text='Whether or not the message was delivered successfully'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, help_text='The owner of this message.'),
            preserve_default=True,
        ),
    ]
