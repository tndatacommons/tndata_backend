# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.utils.text import slugify


def slugify_goal_titles(apps, schema_editor):
    Goal = apps.get_model("goals", "Goal")
    for goal in Goal.objects.all():
        if not goal.title:
            goal.title = goal.name
        goal.title_slug = slugify(goal.title)
        goal.save()


def reverse_goal_titles(apps, schema_editor):
    Goal = apps.get_model("goals", "Goal")
    for goal in Goal.objects.all():
        # NOTE: only partially reversable.. because we can't know if
        # titles were set.
        goal.title_slug = None
        goal.save()


class Migration(migrations.Migration):
    """Fill content for Goal.title_slug."""
    dependencies = [
        ('goals', '0013_auto_20150304_1449'),
    ]

    operations = [
        migrations.RunPython(slugify_goal_titles, reverse_code=reverse_goal_titles),
    ]
