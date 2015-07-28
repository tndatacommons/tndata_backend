# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0059_auto_20150727_2159'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackageEnrollment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('accepted', models.BooleanField(default=False)),
                ('enrolled_on', models.DateTimeField(auto_now_add=True)),
                ('categories', models.ManyToManyField(to='goals.Category')),
                ('enrolled_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='enrolled')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['enrolled_on'],
                'verbose_name': 'Package Enrollment',
                'verbose_name_plural': 'Package Enrollments',
            },
        ),
    ]
