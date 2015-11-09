# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0092_auto_20151106_2145'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='package_contributors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, help_text='The group of users that will contribute to content in this category.', related_name='packagecontributor_set'),
        ),
    ]
