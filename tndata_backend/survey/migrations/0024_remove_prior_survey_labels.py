# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_prior_survey_labels(apps, schema_editor):
    """We've just used the Category information from the goals app to create
    labels, so let's remove any of the pre-existing labels from questions,
    since they are now irrelevant.

    """
    for q in apps.get_model("survey", "BinaryQuestion").objects.all():
        q.labels.clear()

    for q in apps.get_model("survey", "LikertQuestion").objects.all():
        q.labels.clear()

    for q in apps.get_model("survey", "MultipleChoiceQuestion").objects.all():
        q.labels.clear()

    for q in apps.get_model("survey", "OpenEndedQuestion").objects.all():
        q.labels.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0023_auto_20150427_1027'),
    ]

    operations = [
        migrations.RunPython(remove_prior_survey_labels),
    ]
