# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def remove_gcmmessages(apps, schema_editor):
    """Removes all GCMMessage objects. This clears the message queue before
    running a migration that might result in an IntegrityError."""
    GCMMessage = apps.get_model("notifications", "GCMMessage")
    for msg in GCMMessage.objects.all():
        msg.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0014_gcmdevice_device_id'),
    ]

    operations = [
        migrations.RunPython(remove_gcmmessages),
    ]
