# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0074_auto_20150909_1553'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='prevent_custom_triggers_display',
            new_name='display_prevent_custom_triggers_option',
        ),
    ]
