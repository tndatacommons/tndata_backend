# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    replaces = [('notifications', '0001_initial'), ('notifications', '0002_auto_20150401_1447'), ('notifications', '0003_auto_20150401_1558')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GCMMessage',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
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
                'ordering': ['deliver_on'],
                'verbose_name': 'GCM Message',
                'verbose_name_plural': 'GCM Messages',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='gcmmessage',
            unique_together=set([('registration_id', 'message_id')]),
        ),
        migrations.RemoveField(
            model_name='gcmmessage',
            name='scheduled',
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='success',
            field=models.NullBooleanField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='content',
            field=jsonfield.fields.JSONField(help_text='JSON content for the message'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='deliver_on',
            field=models.DateTimeField(help_text='Date/Time on which the message should be delivered', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='expire_on',
            field=models.DateTimeField(null=True, help_text='Date/Time on which this message should expire (be deleted)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='message_id',
            field=models.CharField(help_text='Unique ID for this message.', db_index=True, max_length=32),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='registration_id',
            field=models.CharField(help_text='The Android device ID', db_index=True, max_length=256),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='success',
            field=models.NullBooleanField(help_text='Whether or not the message was delivered successfully'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gcmmessage',
            name='user',
            field=models.ForeignKey(help_text='The owner of this message.', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
