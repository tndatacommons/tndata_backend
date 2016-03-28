# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def set_action_notification_text(apps, schema_editor):
    """Updating Action.notification_text for all Actions."""
    Action = apps.get_model("goals", "Action")
    for action in Action.objects.all():
        text = action.notification_text
        if text and text[0].isupper() and not text[1].isupper():
            text = "{}{}".format(text[0:1].lower(), text[1:])
        action.notification_text = "You can {}".format(text)
        action.save()


class Migration(migrations.Migration):
    dependencies = [
        ('goals', '0130_convert_triggers_to_dynamic'),
    ]
    operations = [
        migrations.RunPython(set_action_notification_text)
    ]
