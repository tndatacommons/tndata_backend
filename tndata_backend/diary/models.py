from django.conf import settings
from django.db import models

from business_rules.actions import BaseActions, rule_action
from business_rules.variables import BaseVariables
from business_rules.variables import (
    boolean_rule_variable,
    numeric_rule_variable,
    string_rule_variable
)
from rules.rulesets import ModelRuleset, ruleset


class Entry(models.Model):
    """An Entry in the Diary"""

    GREAT = 5
    WELL = 4
    FINE = 3
    BAD = 2
    AWFUL = 1

    FEELING_CHOICES = (
        (GREAT, 'Great'),
        (WELL, 'Well'),
        (FINE, 'Just Fine'),
        (BAD, 'Bad'),
        (AWFUL, 'Awful'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    rank = models.PositiveIntegerField(choices=FEELING_CHOICES, db_index=True)
    notes = models.TextField(
        blank=True,
        help_text="Notes on why you are feeling this way."
    )
    submitted_on = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.get_rank_display()

    class Meta:
        ordering = ['submitted_on']
        verbose_name = "Entry"
        verbose_name_plural = "Entries"

    @property
    def rank_display(self):
        return self.get_rank_display()


class EntryVariables(BaseVariables):
    """Exposes a `Entry` data as business-rules variables."""
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
    """Exposes a `Entry` data as business-rules actions."""
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
    """Combines the variables and actions for the `Entry` model's set of rules"""
    model = Entry  # OR, queryset = Entry.objects.filter(...)
    variables = EntryVariables
    actions = EntryActions
    stop_on_first_trigger = False

# NOTE: The register command needs to be in models so it gets picked up.
ruleset.register('diary', EntryRuleset)
