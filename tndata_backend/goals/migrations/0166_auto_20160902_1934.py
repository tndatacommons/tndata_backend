# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-02 19:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0165_auto_20160902_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercompletedcustomaction',
            name='goal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goals.Goal'),
        ),
        migrations.AlterField(
            model_name='usercompletedcustomaction',
            name='customgoal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goals.CustomGoal'),
        ),
    ]
