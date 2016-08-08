# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0155_category_hide_from_organizations'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='contributors',
            field=models.ManyToManyField(help_text='The group of users that will contribute to content in this category.', to=settings.AUTH_USER_MODEL, blank=True, related_name='category_contributions'),
        ),
    ]
