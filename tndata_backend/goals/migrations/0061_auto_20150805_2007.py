# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0060_packageenrollment'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='package_contributors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, help_text='The group of users that will contribute to content in this category.', blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='packaged_content',
            field=models.BooleanField(default=False, help_text='Is this Category for a collection of packaged content?'),
        ),
    ]
