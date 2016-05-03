# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def reset_frequencies(apps, schema_editor):
    Trigger = apps.get_model("goals", "Trigger")
    Trigger.objects.filter(frequency="monthly").update(frequency="biweekly")


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0138_auto_20160420_2029'),
    ]

    operations = [
        migrations.RunPython(reset_frequencies)
    ]
