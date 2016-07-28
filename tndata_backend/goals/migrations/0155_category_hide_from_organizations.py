# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0154_program'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='hide_from_organizations',
            field=models.BooleanField(help_text='Do not show this category to users who are members of an Organization.', default=False),
        ),
    ]
