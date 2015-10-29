# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FunContent',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('message_type', models.CharField(db_index=True, max_length='32', choices=[('quote', 'Quote'), ('fortune', 'Fortune'), ('fact', 'Fun Fact'), ('joke', 'Joke')])),
                ('message', models.TextField(blank=True, help_text='The main content. This could be the quote, joke, forture, etc')),
                ('author', models.CharField(max_length=256, blank=True, help_text='Author or attribution for a quote', null=True)),
                ('keywords', django.contrib.postgres.fields.ArrayField(size=None, blank=True, default=list, base_field=models.CharField(max_length=32, blank=True))),
            ],
            options={
                'verbose_name_plural': 'Fun Content',
                'verbose_name': 'Fun Content',
                'ordering': ['id'],
            },
        ),
    ]
