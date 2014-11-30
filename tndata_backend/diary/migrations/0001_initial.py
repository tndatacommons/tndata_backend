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
            name='Entry',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('rank', models.PositiveIntegerField(choices=[(5, 'Great'), (4, 'Well'), (3, 'Just Fine'), (2, 'Bad'), (1, 'Awful')], db_index=True)),
                ('notes', models.TextField(help_text='Notes on why you are feeling this way.', blank=True)),
                ('submitted_on', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Entries',
                'ordering': ['submitted_on'],
                'verbose_name': 'Entry',
            },
            bases=(models.Model,),
        ),
    ]
