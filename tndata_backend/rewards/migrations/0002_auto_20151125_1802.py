# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='funcontent',
            name='message_type',
            field=models.CharField(db_index=True, choices=[('quote', 'Quote'), ('fortune', 'Fortune'), ('fact', 'Fun Fact'), ('joke', 'Joke')], max_length=32),
        ),
    ]
