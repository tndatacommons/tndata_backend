# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0058_category_packaged_content'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCompletedAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('action', models.ForeignKey(to='goals.Action')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user', 'action'],
                'verbose_name': 'User Completed Action',
                'verbose_name_plural': 'User Completed Action',
            },
        ),
        migrations.RemoveField(
            model_name='useraction',
            name='completed',
        ),
        migrations.RemoveField(
            model_name='useraction',
            name='completed_on',
        ),
        migrations.AddField(
            model_name='usercompletedaction',
            name='useraction',
            field=models.ForeignKey(to='goals.UserAction'),
        ),
    ]
