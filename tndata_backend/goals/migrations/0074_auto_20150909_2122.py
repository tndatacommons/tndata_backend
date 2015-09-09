# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0073_packageenrollment_updated_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='display_prevent_custom_triggers_option',
            field=models.BooleanField(default=True, help_text='This option determines whether or not package contributors will see the option to prevent custom triggers during user enrollment.'),
        ),
        migrations.AddField(
            model_name='category',
            name='prevent_custom_triggers_default',
            field=models.BooleanField(default=False, help_text='This option determines whether or not custom triggers will be allowed by default when enrolling users in the package.'),
        ),
    ]
