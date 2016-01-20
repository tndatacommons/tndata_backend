# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0110_action_serialized_default_trigger'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customaction',
            name='custom_trigger',
            field=models.ForeignKey(blank=True, null=True, to='goals.Trigger', editable=False),
        ),
        migrations.AlterField(
            model_name='customaction',
            name='customgoal',
            field=models.ForeignKey(help_text='The custom goal to which this action belongs', to='goals.CustomGoal'),
        ),
        migrations.AlterField(
            model_name='customaction',
            name='notification_text',
            field=models.CharField(max_length=256, help_text="The text that will be displayed in the app's push notification"),
        ),
        migrations.AlterField(
            model_name='customaction',
            name='title',
            field=models.CharField(db_index=True, max_length=128, help_text='A title for your custom action'),
        ),
        migrations.AlterField(
            model_name='customaction',
            name='title_slug',
            field=models.SlugField(max_length=128, editable=False),
        ),
        migrations.AlterField(
            model_name='customaction',
            name='user',
            field=models.ForeignKey(help_text='The user to which this action belongs.', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='customgoal',
            name='title',
            field=models.CharField(db_index=True, max_length=128, help_text='A title for your Goal.'),
        ),
        migrations.AlterField(
            model_name='customgoal',
            name='title_slug',
            field=models.SlugField(max_length=128, editable=False),
        ),
        migrations.AlterField(
            model_name='customgoal',
            name='user',
            field=models.ForeignKey(help_text='The user to which this goal belongs', to=settings.AUTH_USER_MODEL),
        ),
    ]
