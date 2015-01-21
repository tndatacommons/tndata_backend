# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='notes',
            field=models.TextField(help_text='Additional notes regarding this Category', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='source_link',
            field=models.URLField(null=True, help_text='A link to the source.', blank=True, max_length=256),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='source_name',
            field=models.CharField(null=True, help_text='The name of the source from which this information was adapted.', blank=True, max_length=128),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='notes',
            field=models.TextField(help_text='Additional notes regarding this Category', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interest',
            name='notes',
            field=models.TextField(help_text='Additional notes regarding this Category', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interest',
            name='source_link',
            field=models.URLField(null=True, help_text='A link to the source.', blank=True, max_length=256),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interest',
            name='source_name',
            field=models.CharField(null=True, help_text='The name of the source from which this information was adapted.', blank=True, max_length=128),
            preserve_default=True,
        ),
    ]
