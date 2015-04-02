from django.apps import AppConfig
from django.apps import apps as django_apps

from rules.rulesets import ruleset
from . rulesets import ActionRuleset, BehaviorRuleset, GoalRuleset


class GoalsConfig(AppConfig):
    name = 'goals'
    verbose_name = "Goals"

    def ready(self):
        """Register all of our business-rules rulesets."""
        ruleset.register(self.name, GoalRuleset)
        ruleset.register(self.name, BehaviorRuleset)
        ruleset.register(self.name, ActionRuleset)
