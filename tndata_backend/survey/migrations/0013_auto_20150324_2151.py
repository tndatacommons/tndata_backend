# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0012_binaryquestion_binaryresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='binaryquestion',
            name='priority',
            field=models.PositiveIntegerField(default=0, help_text='When specified, all questions with a priority of 1 will be delivered to users before any questions of priority 2, and so on...'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='likertquestion',
            name='priority',
            field=models.PositiveIntegerField(default=0, help_text='When specified, all questions with a priority of 1 will be delivered to users before any questions of priority 2, and so on...'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiplechoicequestion',
            name='priority',
            field=models.PositiveIntegerField(default=0, help_text='When specified, all questions with a priority of 1 will be delivered to users before any questions of priority 2, and so on...'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openendedquestion',
            name='priority',
            field=models.PositiveIntegerField(default=0, help_text='When specified, all questions with a priority of 1 will be delivered to users before any questions of priority 2, and so on...'),
            preserve_default=True,
        ),
    ]
