# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0140_auto_20160426_1805'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'permissions': (('view_category', 'Can view Categories'), ('decline_category', 'Can Decline Categories'), ('publish_category', 'Can Publish Categories')), 'verbose_name_plural': 'Categories', 'ordering': ['order', 'title', 'enrolled_when_selected'], 'verbose_name': 'Category'},
        ),
        migrations.AddField(
            model_name='category',
            name='enrolled_when_selected',
            field=models.BooleanField(help_text="When a user selects this public category, they are enrolled in all of the category's child content.", default=False),
        ),
    ]
