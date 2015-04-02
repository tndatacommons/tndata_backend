from business_rules.actions import BaseActions, rule_action
from business_rules.variables import BaseVariables
from business_rules.variables import (
    boolean_rule_variable,
    numeric_rule_variable,
    string_rule_variable
)
from rules.rulesets import ModelRuleset
from . models import BinaryResponse

# NOTE: After createing a ModelRulset subclass, you need to register it in the
# AppConfig.ready method.

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
    model = BinaryResponse
    variables = BinaryResponseVariables
    actions = BinaryResponseActions
    stop_on_first_trigger = False
