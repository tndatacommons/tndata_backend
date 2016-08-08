# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def copy_package_contributors_to_contributors(apps, schema_editor):
    Category = apps.get_model("goals", "Category")
    for cat in Category.objects.all():
        for user in cat.package_contributors.all():
            cat.contributors.add(user)
        cat.save()


def copy_contributors_to_package_contributors(apps, schema_editor):
    Category = apps.get_model("goals", "Category")
    for cat in Category.objects.all():
        for user in cat.contributors.all():
            cat.package_contributors.add(user)
        cat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0156_category_contributors'),
    ]

    operations = [
        migrations.RunPython(
            copy_package_contributors_to_contributors,
            reverse_code=copy_contributors_to_package_contributors
        ),
    ]
