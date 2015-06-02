# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0047_auto_20150531_1646'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryProgress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('current_score', models.FloatField(default=0)),
                ('reported_on', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(to='goals.Category')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Category Progress',
                'verbose_name_plural': 'Category Progression',
                'get_latest_by': 'reported_on',
                'ordering': ['-reported_on'],
            },
        ),
    ]
