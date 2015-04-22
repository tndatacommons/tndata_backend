# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from ..permissions import (
    get_or_create_content_authors,
    get_or_create_content_editors,
)


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0032_auto_20150416_1048'),
        ('auth', '__first__'),
    ]

    operations = [
        migrations.RunPython(get_or_create_content_authors),
        migrations.RunPython(get_or_create_content_editors),
    ]
