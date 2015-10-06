# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations


def set_usergoal(apps, schema_editor):
    """Fill in values for GoalProgress.usergoal when that field is null"""
    GoalProgress = apps.get_model("goals", "GoalProgress")
    UserGoal = apps.get_model("goals", "UserGoal")
    for gp in GoalProgress.objects.filter(usergoal__isnull=True):
        ug = UserGoal.objects.filter(user=gp.user, goal=gp.goal).first()
        if ug:
            gp.usergoal = ug
            gp.save()


def unset_usergoal(apps, schema_editor):
    """Set all values for GoalProgress.usergoal to null"""
    GoalProgress = apps.get_model("goals", "GoalProgress")
    GoalProgress.objects.update(usergoal=None)


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0081_auto_20151006_1826'),
    ]

    operations = [
        migrations.RunPython(set_usergoal, reverse_code=unset_usergoal),
    ]
