# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0141_auto_20160427_2112'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['order', 'title', 'featured'], 'verbose_name': 'Category', 'permissions': (('view_category', 'Can view Categories'), ('decline_category', 'Can Decline Categories'), ('publish_category', 'Can Publish Categories')), 'verbose_name_plural': 'Categories'},
        ),
        migrations.RemoveField(
            model_name='category',
            name='enrolled_when_selected',
        ),
        migrations.AddField(
            model_name='category',
            name='featured',
            field=models.BooleanField(help_text='Featured categories are typically collection of content provided by an agency/partner that we want to promote publicy within the app.', default=False),
        ),
    ]
