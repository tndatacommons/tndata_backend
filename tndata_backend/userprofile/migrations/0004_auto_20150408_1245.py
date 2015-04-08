# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0003_userprofile_created_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='children',
            field=models.CharField(blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='economic_aspiration',
            field=models.CharField(blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='employment_status',
            field=models.CharField(blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='birthdate',
            field=models.DateField(blank=True, null=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='educational_level',
            field=models.CharField(blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, max_length=128, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='marital_status',
            field=models.CharField(blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='race',
            field=models.CharField(blank=True, max_length=128, db_index=True),
            preserve_default=True,
        ),
    ]
