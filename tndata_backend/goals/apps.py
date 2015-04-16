from django.apps import AppConfig
from rules.rulesets import ruleset

from . permissions import (
    get_or_create_content_authors,
    get_or_create_content_editors,
)
from . rulesets import ActionRuleset, BehaviorRuleset, GoalRuleset


class GoalsConfig(AppConfig):
    name = 'goals'
    verbose_name = "Goals"

    def ready(self):
        """Register all of our business-rules rulesets and ensure that
        appropriate groups have been created."""

        # Register the rules.
        ruleset.register(self.name, GoalRuleset)
        ruleset.register(self.name, BehaviorRuleset)
        ruleset.register(self.name, ActionRuleset)

        # Create Groups if needed.
        # NOTE: We really should do anything that writes to the DB here because
        # this gets run on every management command: http://goo.gl/Idtz8F
        # I have no idea where else to programmatically create Groups, though :(
        get_or_create_content_authors()
        get_or_create_content_editors()
