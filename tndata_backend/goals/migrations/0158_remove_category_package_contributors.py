# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0157_copy_package_contributors'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='package_contributors',
        ),
    ]
