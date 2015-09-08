# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


# Some initial, primary places.
PLACES = [
    ('Work', 'work'),
    ('Home', 'home'),
    ('School', 'school'),
]


def create_primary_place(apps, schema_editor=None):
    Place = apps.get_model("userprofile", "Place")
    for name, slug in PLACES:
        Place.objects.create(name=name, slug=slug, primary=True)


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0010_auto_20150908_2010'),
    ]

    operations = [
        migrations.RunPython(create_primary_place),
    ]
