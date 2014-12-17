# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('app_name', models.CharField(max_length=256, db_index=True)),
                ('rule_name', models.CharField(max_length=256, blank=True)),
                ('conditions', jsonfield.fields.JSONField(db_index=True)),
                ('actions', jsonfield.fields.JSONField(db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
            ],
            options={
                'ordering': ['app_name', 'created'],
                'verbose_name_plural': 'Rules',
                'verbose_name': 'Rule',
            },
            bases=(models.Model,),
        ),
    ]
