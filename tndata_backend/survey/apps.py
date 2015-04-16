from django.apps import AppConfig
from django.apps import apps as django_apps

from rules.rulesets import ruleset
from . permissions import get_or_create_survey_admins_group
from . rulesets import BinaryResponseRuleset


class SurveyConfig(AppConfig):
    name = 'survey'
    verbose_name = "Survey"

    def ready(self):
        """Register all of our business-rules rulesets and ensure that
        appropriate groups have been created."""

        # Register the rules
        ruleset.register(self.name, BinaryResponseRuleset)

        # Create Groups if needed.
        # NOTE: We really should do anything that writes to the DB here because
        # this gets run on every management command: http://goo.gl/Idtz8F
        # I have no idea where else to programmatically create Groups, though :(
        get_or_create_survey_admins_group()
