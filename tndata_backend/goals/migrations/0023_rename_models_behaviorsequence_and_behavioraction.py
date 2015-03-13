# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations

# Renaming the BehaviorSequence -> Behavior, and BehaviorAction -> Action.
#
# Tables/Sequences before:
#
#  goals_behavioraction
#  goals_behaviorsequence
#  goals_behaviorsequence_categories
#  goals_behaviorsequence_goals
#
#  goals_behavioraction_id_seq
#  goals_behaviorsequence_categories_id_seq
#  goals_behaviorsequence_goals_id_seq
#  goals_behaviorsequence_id_seq
#
# Expected tables/sequences after:
#
#  goals_action
#  goals_behavior
#  goals_behavior_categories
#  goals_behavior_goals
#
#  goals_action_id_seq
#  goals_behavior_categories_id_seq
#  goals_behavior_goals_id_seq
#  goals_behavior_id_seq


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0022_auto_20150312_1822'),
    ]
    operations = [
        migrations.RenameField('BehaviorAction', 'sequence', 'behavior'),
        migrations.RenameModel("BehaviorSequence", "Behavior"),
        migrations.RenameModel("BehaviorAction", "Action"),

        # Rename the sequences that exist for the intermediary models.
        # ALTER SEQUENCE [ IF EXISTS ] name RENAME TO new_name
        migrations.RunSQL("ALTER SEQUENCE IF EXISTS goals_behavioraction_id_seq RENAME TO goals_action_id_seq"),
        migrations.RunSQL("ALTER SEQUENCE IF EXISTS goals_behaviorsequence_id_seq RENAME TO goals_behavior_id_seq"),
        migrations.RunSQL("ALTER SEQUENCE IF EXISTS goals_behaviorsequence_categories_id_seq RENAME TO goals_behavior_categories_id_seq"),
        migrations.RunSQL("ALTER SEQUENCE IF EXISTS goals_behaviorsequence_goals_id_seq RENAME TO goals_behavior_goals_id_seq"),
    ]
