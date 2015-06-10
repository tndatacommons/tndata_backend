# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0048_categoryprogress'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='user',
            field=models.ForeignKey(blank=True, null=True, to=settings.AUTH_USER_MODEL, help_text='A Custom trigger, created by a user.'),
        ),
    ]
