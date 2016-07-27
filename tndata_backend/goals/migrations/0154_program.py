# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0153_category_organizations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(help_text="The program's name.", max_length=512, unique=True)),
                ('name_slug', models.SlugField(max_length=512, unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('auto_enrolled_goals', models.ManyToManyField(to='goals.Goal', help_text='The goals in which program members will be auto-enrolled.')),
                ('categories', models.ManyToManyField(to='goals.Category', help_text='The categories from which content in this program will be available.')),
                ('members', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, help_text='Users who are signed up for this program (e.g. students)')),
                ('organization', models.ForeignKey(to='goals.Organization', help_text='The organziation to which this program is associated')),
            ],
            options={
                'ordering': ['organization', 'name'],
                'verbose_name': 'Program',
                'verbose_name_plural': 'Programs',
            },
        ),
    ]
