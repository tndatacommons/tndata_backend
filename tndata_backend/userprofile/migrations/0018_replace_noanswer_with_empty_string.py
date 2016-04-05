# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def replace_noanswer_with_empty_string(apps, schema_editor=None):
    # The user's profile model, where we want to save data.
    UserProfile = apps.get_model("userprofile", "UserProfile")
    for up in UserProfile.objects.all():
        if up.sex == "no-answer":
            up.sex = ""
            up.save()


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0017_copy_profile_fields_from_survey'),
    ]

    operations = [
        migrations.RunPython(replace_noanswer_with_empty_string),
    ]
