# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def count_behavior_actions(apps, schema_editor):
    """Count the child actions for each behavior, and record the bucket types."""
    Action = apps.get_model("goals", "Action")
    Behavior = apps.get_model("goals", "Behavior")

    for behavior in Behavior.objects.all():
        actions = Action.objects.filter(behavior__id=behavior.id)
        behavior.action_buckets_prep = actions.filter(bucket='prep').count()
        behavior.action_buckets_core = actions.filter(bucket='core').count()
        behavior.action_buckets_helper = actions.filter(bucket='helper').count()
        behavior.action_buckets_checkup = actions.filter(bucket='checkup').count()
        behavior.save()

class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0133_auto_20160411_2019'),
    ]

    operations = [
        migrations.RunPython(count_behavior_actions)
    ]
