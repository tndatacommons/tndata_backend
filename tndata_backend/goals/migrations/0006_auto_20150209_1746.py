# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_interestgroup_categories_into_interest(apps, schema_editor):
    """We've just added `categories` to the Interest model, now we need to
    directly connect Interest <-> Category using the info that's already stored
    in InterestGroup."""
    InterestGroup = apps.get_model("goals", "InterestGroup")
    for group in InterestGroup.objects.all():
        for interest in group.interests.all():
            interest.categories.add(group.category)
            interest.save()


class Migration(migrations.Migration):
    """Data migration to Associate Category <-> Interest based on the
    existing InterestGroup models.

    See https://docs.djangoproject.com/en/1.7/topics/migrations/#data-migrations
    """

    dependencies = [
        ('goals', '0005_interest_categories'),
    ]

    operations = [
        migrations.RunPython(copy_interestgroup_categories_into_interest),
    ]
