# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0029_auto_20150413_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='state',
            field=django_fsm.FSMField(default='draft', max_length=50),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavior',
            name='state',
            field=django_fsm.FSMField(default='draft', max_length=50),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='state',
            field=django_fsm.FSMField(default='draft', max_length=50),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='goal',
            name='state',
            field=django_fsm.FSMField(default='draft', max_length=50),
            preserve_default=True,
        ),
    ]
