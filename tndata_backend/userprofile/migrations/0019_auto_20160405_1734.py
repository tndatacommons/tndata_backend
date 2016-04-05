# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0018_replace_noanswer_with_empty_string'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(blank=True, max_length=32, choices=[('female', 'Female'), ('male', 'Male'), ('', 'Prefer not to answer')], default=''),
        ),
    ]
