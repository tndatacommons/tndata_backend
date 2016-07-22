# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0152_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='organizations',
            field=models.ManyToManyField(to='goals.Organization', help_text='Organizations whose members should have access to this content.', related_name='categories', blank=True),
        ),
    ]
