# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0079_auto_20151005_1933'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='behaviorprogress',
            options={'get_latest_by': 'reported_on', 'ordering': ['-reported_on'], 'verbose_name_plural': 'Behavior Progresses', 'verbose_name': 'Behavior Progress'},
        ),
        migrations.AlterModelOptions(
            name='categoryprogress',
            options={'get_latest_by': 'reported_on', 'ordering': ['-reported_on'], 'verbose_name_plural': 'Category Progresses', 'verbose_name': 'Category Progress'},
        ),
        migrations.AlterModelOptions(
            name='goalprogress',
            options={'get_latest_by': 'reported_on', 'ordering': ['-reported_on'], 'verbose_name_plural': 'Goal Progresses', 'verbose_name': 'Goal Progress'},
        ),
    ]
