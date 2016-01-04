# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0106_useraction_serialized_trigger'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='case',
        ),
        migrations.RemoveField(
            model_name='action',
            name='image',
        ),
        migrations.RemoveField(
            model_name='action',
            name='outcome',
        ),
        migrations.RemoveField(
            model_name='behavior',
            name='case',
        ),
        migrations.RemoveField(
            model_name='behavior',
            name='default_trigger',
        ),
        migrations.RemoveField(
            model_name='behavior',
            name='image',
        ),
        migrations.RemoveField(
            model_name='behavior',
            name='notification_text',
        ),
        migrations.RemoveField(
            model_name='behavior',
            name='outcome',
        ),
    ]
