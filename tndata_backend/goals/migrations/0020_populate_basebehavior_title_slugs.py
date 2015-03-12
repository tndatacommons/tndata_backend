# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.utils.text import slugify


def _copy_name_to_title(model, apps):
    """Copy the values from the Model's name -> title and name_slug -> title_slug."""
    M = apps.get_model("goals", model)
    for obj in M.objects.all():
        obj.title = obj.name
        obj.title_slug = obj.name_slug or slugify(obj.name)
        obj.save()


def _copy_title_to_name(model, apps):
    """Copy the values from the Model's title -> name and title_slug -> name_slug."""
    M = apps.get_model("goals", model)
    for obj in M.objects.all():
        obj.name = obj.title
        obj.name_slug = obj.title_slug or slugify(obj.title)
        obj.save()


def copy_behavior_title(apps, schema_editor):
    _copy_name_to_title("BehaviorSequence", apps)


def copy_action_title(apps, schema_editor):
    _copy_name_to_title("BehaviorAction", apps)


def rev_copy_behavior_title(apps, schema_editor):
    _copy_title_to_name("BehaviorSequence", apps)


def rev_copy_action_title(apps, schema_editor):
    _copy_title_to_name("BehaviorAction", apps)


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0019_auto_20150312_1553'),
    ]

    operations = [
        migrations.RunPython(copy_behavior_title, reverse_code=rev_copy_behavior_title),
        migrations.RunPython(copy_action_title, reverse_code=rev_copy_action_title),
    ]
