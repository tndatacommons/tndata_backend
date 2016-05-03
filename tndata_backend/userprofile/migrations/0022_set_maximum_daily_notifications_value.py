# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def set_max_notifications(apps, schema_editor=None):
    UserProfile = apps.get_model("userprofile", "UserProfile")
    for up in UserProfile.objects.all():
        up.maximum_daily_notifications = 5
        up.save()


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0021_auto_20160419_2131'),
    ]

    operations = [
        migrations.RunPython(set_max_notifications),
    ]
