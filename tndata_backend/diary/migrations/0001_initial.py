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
            name='Feeling',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('rank', models.PositiveIntegerField(db_index=True, choices=[(5, 'Great'), (4, 'Well'), (3, 'Just Fine'), (2, 'Bad'), (1, 'Awful')])),
                ('notes', models.TextField(help_text='Notes on why you are feeling this way.', blank=True)),
                ('submitted_on', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Feelings',
                'verbose_name': 'Feeling',
                'ordering': ['submitted_on'],
            },
            bases=(models.Model,),
        ),
    ]
