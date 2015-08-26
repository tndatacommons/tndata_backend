# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0070_auto_20150819_2256'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageenrollment',
            name='prevent_custom_triggers',
            field=models.BooleanField(help_text='Setting this option will prevent users from overriding the default reminder times for actions within the selected goals.', default=False),
        ),
    ]
