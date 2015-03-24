# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def _get_user_ids(model):
    """Get a list of unique users attached to the given model."""
    return model.objects.values_list("user", flat=True).distinct("user")


def _delete_secondary_items(model):
    for uid in _get_user_ids(model):
        instances = model.objects.filter(user__id=uid).order_by("created_on")
        for obj in instances[1:]:
            obj.delete()


def delete_secondary_usercategories(apps, schema_editor):
    _delete_secondary_items(apps.get_model("goals", "UserCategory"))


def delete_secondary_usergoals(apps, schema_editor):
    _delete_secondary_items(apps.get_model("goals", "UserGoal"))


def delete_secondary_userbehaviors(apps, schema_editor):
    _delete_secondary_items(apps.get_model("goals", "UserBehavior"))


def delete_secondary_useractions(apps, schema_editor):
    _delete_secondary_items(apps.get_model("goals", "UserAction"))


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0026_usercategory'),
    ]

    operations = [
        migrations.RunPython(delete_secondary_usercategories),
        migrations.RunPython(delete_secondary_usergoals),
        migrations.RunPython(delete_secondary_userbehaviors),
        migrations.RunPython(delete_secondary_useractions),
    ]
