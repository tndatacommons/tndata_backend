# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0147_category_grouping'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Category', 'permissions': (('view_category', 'Can view Categories'), ('decline_category', 'Can Decline Categories'), ('publish_category', 'Can Publish Categories')), 'ordering': ['grouping', 'order', 'title'], 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterField(
            model_name='category',
            name='grouping',
            field=models.IntegerField(default=-1, choices=[(-1, 'General'), (0, 'Get ready for college'), (1, 'Succeed in College'), (2, 'Help your student succeed')], blank=True, null=True),
        ),
    ]
