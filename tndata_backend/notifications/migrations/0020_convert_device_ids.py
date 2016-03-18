# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models

import hashlib


def make_hash(input_string):
    m = hashlib.md5()
    m.update(input_string.encode("utf8"))
    return m.hexdigest()


def convert_device_ids(apps, schema_editor):
    GCMDevice = apps.get_model('notifications', 'GCMDevice')
    for device in GCMDevice.objects.all():
        try:
            name = device.device_name or 'unkown'
            value = "{}+{}".format(device.user.email, name)
            device.device_id = make_hash(value)
            device.save()
        except:
            pass  # oh well


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0019_auto_20160212_1940'),
    ]

    operations = [
        migrations.RunPython(convert_device_ids)
    ]
