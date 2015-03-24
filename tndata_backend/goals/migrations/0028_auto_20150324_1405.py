# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0027_dedup_user_associations'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='useraction',
            unique_together=set([('user', 'action')]),
        ),
        migrations.AlterUniqueTogether(
            name='userbehavior',
            unique_together=set([('user', 'behavior')]),
        ),
        migrations.AlterUniqueTogether(
            name='usercategory',
            unique_together=set([('user', 'category')]),
        ),
        migrations.AlterUniqueTogether(
            name='usergoal',
            unique_together=set([('user', 'goal')]),
        ),
    ]
