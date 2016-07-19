# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0151_remove_goal_outcome'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(help_text="The organization's official name", unique=True, max_length=512)),
                ('name_slug', models.SlugField(unique=True, max_length=512)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('admins', models.ManyToManyField(related_name='admin_organizations', help_text='Users who are admins of this organization', blank=True, to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(related_name='member_organizations', help_text='Users who are members of this organization (e.g. students)', blank=True, to=settings.AUTH_USER_MODEL)),
                ('staff', models.ManyToManyField(related_name='staff_organizations', help_text='Users who are staff this organization', blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Organizations',
                'verbose_name': 'Organization',
                'ordering': ['name'],
            },
        ),
    ]
