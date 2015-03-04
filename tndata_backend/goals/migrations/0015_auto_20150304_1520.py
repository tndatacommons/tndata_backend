# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0014_slugify_goal_titles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='goal',
            name='name',
        ),
        migrations.RemoveField(
            model_name='goal',
            name='name_slug',
        ),
    ]
