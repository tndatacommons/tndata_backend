# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def preserialize_usergoals(apps, schema_editor):
    UserGoal = apps.get_model("goals", "UserGoal")
    for ug in UserGoal.objects.all():
        ug.save()


def preserialize_useractions(apps, schema_editor):
    UserAction = apps.get_model("goals", "UserAction")
    for ua in UserAction.objects.all():
        ua.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0104_auto_20151218_2222'),
    ]

    operations = [
        migrations.RunPython(preserialize_usergoals),
        migrations.RunPython(preserialize_useractions),
    ]
