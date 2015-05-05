# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from .. permissions import CONTENT_AUTHORS, CONTENT_EDITORS


def _get_group_and_permission(apps):
    return (
        apps.get_model("auth", "Group"),
        apps.get_model("auth", "Permission")
    )


def create_content_authors(apps, schema_editor=None):
    Group, Permission = _get_group_and_permission(apps)
    group, created = Group.objects.get_or_create(name=CONTENT_AUTHORS)
    perms = [
        "view_category",
        "view_trigger",
    ]
    for obj in ['goal', 'behavior', 'action']:
        perms.append("add_{0}".format(obj))
        perms.append("change_{0}".format(obj))
        perms.append("view_{0}".format(obj))
    for p in Permission.objects.filter(codename__in=perms):
        group.permissions.add(p)
    group.save()


def create_content_editors(apps, schema_editor=None):
    Group, Permission = _get_group_and_permission(apps)
    group, created = Group.objects.get_or_create(name=CONTENT_EDITORS)
    perms = []
    for obj in ['category', 'goal', 'behavior', 'action', 'trigger']:
        perms.append("add_{0}".format(obj))
        perms.append("change_{0}".format(obj))
        perms.append("view_{0}".format(obj))
        perms.append("delete_{0}".format(obj))
        perms.append("publish_{0}".format(obj))
        perms.append("decline_{0}".format(obj))
    for p in Permission.objects.filter(codename__in=perms):
        group.permissions.add(p)
    group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0032_auto_20150416_1048'),
        ('auth', '__first__'),
    ]

    operations = [
        migrations.RunPython(create_content_authors),
        migrations.RunPython(create_content_editors),
    ]
