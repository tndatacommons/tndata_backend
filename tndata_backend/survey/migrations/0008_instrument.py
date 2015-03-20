# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0007_auto_20150225_2207'),
    ]

    operations = [
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.TextField(unique=True, db_index=True)),
                ('description', models.TextField(help_text='Optional Description for this Instrument')),
            ],
            options={
                'ordering': ['title'],
                'verbose_name_plural': 'Instruments',
                'verbose_name': 'Instrument',
            },
            bases=(models.Model,),
        ),
    ]
