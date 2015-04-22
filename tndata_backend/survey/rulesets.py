from business_rules.actions import BaseActions, rule_action
from business_rules.variables import BaseVariables
from business_rules.variables import (
    boolean_rule_variable,
    string_rule_variable
)
from rules.rulesets import ModelRuleset, ruleset
from . import models


# NOTE: After createing a ModelRulset subclass, you need to register it in the
# AppConfig.ready method.
# TODO: I'm not sure where to call this, so It's currently not getting called
# anywhere. We can't do this in the AppConfig.ready, because this will load
# Models before the app is actually ready.

def register_rules(app_name):
    """Register all of the Rules."""
    ruleset.register(app_name, BinaryResponseRuleset)


# TODO: Need aggregated data for survey responses before this is meaningful.
class BinaryResponseVariables(BaseVariables):
    """Exposes a `BinaryResponse`'s data as business-rules variables."""
    def __init__(self, response):
        self.response = response

    @string_rule_variable()
    def question(self):
        return self.response.question.text

    @boolean_rule_variable()
    def response(self):
        return self.response.selected_option


class BinaryResponseActions(BaseActions):
    def __init__(self, response):
        self.response = response

    # TODO: Figure out what *real* actions we need.
    @rule_action()
    def similar_responses(self):
        print("{0} for {1}".format(
            self.response.selected_option,
            self.response.question
        ))


class BinaryResponseRuleset(ModelRuleset):
    model = models.BinaryResponse
    variables = BinaryResponseVariables
    actions = BinaryResponseActions
    stop_on_first_trigger = False
