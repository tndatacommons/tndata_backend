# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GCMMessage',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('message_id', models.CharField(db_index=True, max_length=32)),
                ('registration_id', models.CharField(db_index=True, max_length=256)),
                ('content', jsonfield.fields.JSONField()),
                ('scheduled', models.DateTimeField(auto_now_add=True)),
                ('success', models.BooleanField(default=False)),
                ('response_code', models.IntegerField(null=True, blank=True)),
                ('response_text', models.CharField(blank=True, max_length=256)),
                ('deliver_on', models.DateTimeField(db_index=True)),
                ('expire_on', models.DateTimeField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'GCM Messages',
                'verbose_name': 'GCM Message',
                'ordering': ['deliver_on'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='gcmmessage',
            unique_together=set([('registration_id', 'message_id')]),
        ),
    ]
