# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-23 19:57
from __future__ import unicode_literals
from django.db import migrations



def add_action_goals(apps, schema_editor):
    Action = apps.get_model("goals", "Action")
    for action in Action.objects.all():
        for goal in action.behavior.goals.all():
            action.goals.add(goal)


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0174_add_action_goals_optional_behavior'),
    ]

    operations = [
        migrations.RunPython(add_action_goals)
    ]
