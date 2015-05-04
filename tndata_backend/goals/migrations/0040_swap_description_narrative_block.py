# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def swap_description_and_narrative_block(apps, schema_editor):
    """Swap the content of the `narrative_block` and `description` fields for
    both Action and Behavior.

    """
    Behavior = apps.get_model("goals", "Behavior")
    Action = apps.get_model("goals", "Action")

    for obj in Behavior.objects.all():
        desc = obj.narrative_block
        obj.narrative_block = obj.description
        obj.description = desc
        obj.save()

    for obj in Action.objects.all():
        desc = obj.narrative_block
        obj.narrative_block = obj.description
        obj.description = desc
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0039_auto_20150501_1332'),
    ]

    operations = [
        migrations.RunPython(
            swap_description_and_narrative_block,
            reverse_code=swap_description_and_narrative_block
        ),
    ]
