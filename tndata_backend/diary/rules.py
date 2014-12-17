# Trying out business-rules
# https://github.com/venmo/business-rules

from business_rules import export_rule_data
from business_rules.actions import BaseActions, rule_action
from business_rules.variables import BaseVariables
from business_rules.variables import (
    boolean_rule_variable,
    numeric_rule_variable,
    string_rule_variable
)

from rules.rulesets import ModelRuleset, ruleset
from . models import Entry


class EntryVariables(BaseVariables):

    def __init__(self, entry):
        self.entry = entry

    @numeric_rule_variable()
    def feeling_ranked(self):
        return self.entry.rank

    @string_rule_variable()
    def submitted_day(self):
        return self.entry.submitted_on.strftime("%A")

    @boolean_rule_variable()
    def is_awful(self):
        return self.entry.rank == 1


class EntryActions(BaseActions):

    def __init__(self, entry):
        self.entry = entry

    @rule_action()
    def log_feeling(self):
        args = (self.entry.id, self.entry.get_rank_display(), self.entry)
        print("Entry {0} is feeling {1}: {2}".format(*args))

    @rule_action()  # NOTE: need the params or this doesn't work.
    def send_notification(self):
        args = (self.entry.id, self.entry)
        print("Have a great Weekend, Entry {0}) {1}".format(*args))


class EntryRuleset(ModelRuleset):
    model = Entry  # OR, queryset = Entry.objects.filter(...)
    variables = EntryVariables
    actions = EntryActions
    stop_on_first_trigger = False
ruleset.register('diary', EntryRuleset)


def entry_rule_data():
    """Generates a Dict describing Variables/Actions for the Entry model."""
    return export_rule_data(EntryVariables, EntryActions)


# -----------------------------------------------------------------------------
# NOTE: The below are example rules, and a sample method to apply them.
# -----------------------------------------------------------------------------
diary_rules = [

    # If feeling_ranked > 3 AND submitted_day == 'Saturday'
    # Then send_notification
    {
        "conditions": {
            "all": [
                {
                    "name": "feeling_ranked",
                    "operator": "greater_than",
                    "value": 3,
                },
                {
                    "name": "submitted_day",
                    "operator": "equal_to",
                    "value": "Saturday",
                },
            ]
        },
        "actions": [
            {
                "name": "send_notification",
                #"fields": [],
            },
        ],
    },

    # If feeling_ranked < 3, log the feeling.
    {
        "conditions": {
            "all": [
                {
                    "name": "feeling_ranked",
                    "operator": "less_than",
                    "value": 3,
                },
            ]
        },
        "actions": [
            {
                "name": "log_feeling",
                #"fields": [],
            },
        ],
    },
]


# Running all the rules
def run_rules():
    from business_rules import run_all
    from . import models

    # NOTE: Presumably we'd do this for entries saved since some time period;
    # e.g. the last day, or the last 2 hours.
    for entry in models.Entry.objects.all():
        run_all(
            rule_list=diary_rules,
            defined_variables=EntryVariables(entry),
            defined_actions=EntryActions(entry),
            stop_on_first_trigger=False
        )
