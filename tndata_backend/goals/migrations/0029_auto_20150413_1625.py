# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('goals', '0028_auto_20150324_1405'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'Categories', 'verbose_name': 'Category', 'ordering': ['order', 'title']},
        ),
        migrations.AddField(
            model_name='action',
            name='created_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='actions_created'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='action',
            name='updated_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='actions_updated'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='behavior',
            name='created_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='behaviors_created'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavior',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='behavior',
            name='updated_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='behaviors_updated'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='behavior',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='created_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='categories_created'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='updated_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='categories_updated'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='goal',
            name='created_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='goals_created'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='goal',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='goal',
            name='updated_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='goals_updated'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='goal',
            name='updated_on',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='behavior',
            name='informal_list',
            field=models.TextField(help_text='A working list of actions for the behavior. Mnemonic only.', blank=True),
            preserve_default=True,
        ),
    ]
