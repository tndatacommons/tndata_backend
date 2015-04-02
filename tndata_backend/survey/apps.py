from django.apps import AppConfig
from django.apps import apps as django_apps

from rules.rulesets import ruleset
from . rulesets import BinaryResponseRuleset


class SurveyConfig(AppConfig):
    name = 'survey'
    verbose_name = "Survey"

    def ready(self):
        """Register all of our business-rules rulesets."""
        ruleset.register(self.name, BinaryResponseRuleset)
