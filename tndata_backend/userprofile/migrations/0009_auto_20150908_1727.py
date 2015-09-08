# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userprofile', '0008_auto_20150730_1554'),
    ]

    operations = [
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(db_index=True, max_length=32, unique=True)),
                ('slug', models.SlugField(max_length=32, unique=True)),
                ('primary', models.BooleanField(default=False, help_text='Use this place as a suggestion for users.')),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Place',
                'verbose_name_plural': 'Places',
            },
        ),
        migrations.CreateModel(
            name='UserPlace',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('latitude', models.DecimalField(db_index=True, decimal_places=4, max_digits=8)),
                ('longitude', models.DecimalField(db_index=True, decimal_places=4, max_digits=8)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('place', models.ForeignKey(to='userprofile.Place')),
                ('profile', models.ForeignKey(to='userprofile.UserProfile')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Place',
                'verbose_name_plural': 'User Places',
            },
        ),
        migrations.AlterOrderWithRespectTo(
            name='userplace',
            order_with_respect_to='user',
        ),
    ]
