# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0017_auto_20150304_1539'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actiontaken',
            name='selected_action',
        ),
        migrations.RemoveField(
            model_name='actiontaken',
            name='user',
        ),
        migrations.DeleteModel(
            name='ActionTaken',
        ),
        migrations.AlterUniqueTogether(
            name='customreminder',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='customreminder',
            name='action',
        ),
        migrations.RemoveField(
            model_name='customreminder',
            name='user',
        ),
        migrations.DeleteModel(
            name='CustomReminder',
        ),
        migrations.RemoveField(
            model_name='selectedaction',
            name='action',
        ),
        migrations.DeleteModel(
            name='Action',
        ),
        migrations.RemoveField(
            model_name='selectedaction',
            name='user',
        ),
        migrations.DeleteModel(
            name='SelectedAction',
        ),
    ]
