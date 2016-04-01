# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def remove_duplicates(apps, schema_editor):
    """We want GCMDevice objects to be unique on
    (user, device_id, registration_id), so this function will find duplicates,
    and remove the older ones.

    """
    GCMDevice = apps.get_model('notifications', 'GCMDevice')
    reg_ids = set(GCMDevice.objects.values_list('registration_id', flat=True))
    for reg_id in reg_ids:
        devices = GCMDevice.objects.filter(registration_id=reg_id).order_by("-updated_on")
        if devices.count() > 1:
            # Slice the list so we keep the most recently-updated and delete the rest
            for device in devices[1:]:
                device.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0020_convert_device_ids'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates)
    ]
