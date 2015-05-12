# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0002_auto_20150506_1951'),
    ]

    operations = [
        migrations.CreateModel(
            name='GCMDevice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('device_name', models.CharField(default='Default Device', help_text='A name for this device', max_length=32, blank=True)),
                ('registration_id', models.CharField(help_text='The Android device ID', max_length=256, db_index=True)),
                ('is_active', models.BooleanField(default=True, help_text='Does this device accept notifications?')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(help_text='The owner of this message.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'GCM Devices',
                'ordering': ['user', 'registration_id'],
                'verbose_name': 'GCM Device',
            },
        ),
        migrations.AlterUniqueTogether(
            name='gcmdevice',
            unique_together=set([('registration_id', 'user')]),
        ),
    ]
