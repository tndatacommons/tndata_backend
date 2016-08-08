# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0158_remove_category_package_contributors'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='hide_from_organizations',
        ),
        migrations.AddField(
            model_name='category',
            name='hidden_from_organizations',
            field=models.ManyToManyField(related_name='excluded_categories', blank=True, help_text='Organizations whose members should NOT be able to view this category.', to='goals.Organization'),
        ),
        migrations.AlterField(
            model_name='category',
            name='grouping',
            field=models.IntegerField(default=-1, blank=True, choices=[(-1, 'General'), (0, 'Get ready for college'), (1, 'Succeed in college'), (2, 'Help your student succeed'), (3, 'Featured')], help_text='This option defines the section within the app where this category will be listed.', null=True),
        ),
    ]
