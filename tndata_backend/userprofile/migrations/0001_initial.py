# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('birthdate', models.DateField(blank=True)),
                ('race', models.CharField(blank=True, max_length=10)),
                ('gender', models.CharField(blank=True, max_length=10)),
                ('marital_status', models.CharField(blank=True, max_length=10)),
                ('educational_level', models.CharField(blank=True, max_length=32)),
                ('mobile_phone', models.CharField(blank=True, max_length=32)),
                ('home_phone', models.CharField(blank=True, max_length=32)),
                ('home_address', models.CharField(blank=True, max_length=32)),
                ('home_city', models.CharField(blank=True, max_length=32)),
                ('home_state', models.CharField(blank=True, max_length=32)),
                ('home_zip', models.CharField(blank=True, max_length=32)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, help_text='The user to whom this profile belongs')),
            ],
            options={
                'verbose_name_plural': 'User Profiles',
                'verbose_name': 'User Profile',
            },
            bases=(models.Model,),
        ),
        migrations.AlterOrderWithRespectTo(
            name='userprofile',
            order_with_respect_to='user',
        ),
    ]
