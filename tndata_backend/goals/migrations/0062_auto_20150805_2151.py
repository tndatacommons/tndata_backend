# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0061_auto_20150805_2007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='packageenrollment',
            name='categories',
        ),
        migrations.AddField(
            model_name='packageenrollment',
            name='category',
            field=models.ForeignKey(default=1, to='goals.Category'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='packageenrollment',
            name='goals',
            field=models.ManyToManyField(to='goals.Goal'),
        ),
    ]
