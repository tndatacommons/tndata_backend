# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from ..permissions import get_or_create_survey_admins_group


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0018_openendedquestion_input_type'),
        ('auth', '__first__'),
    ]

    operations = [
        migrations.RunPython(get_or_create_survey_admins_group),
    ]
