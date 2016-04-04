# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0015_userprofile_maximum_daily_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='birthday',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='employed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_degree',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='in_relationship',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_parent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(max_length=32, null=True, choices=[('female', 'Female'), ('male', 'Male'), ('no-answer', 'Prefer not to answer')], blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='zipcode',
            field=models.CharField(max_length=32, null=True, blank=True),
        ),
    ]
