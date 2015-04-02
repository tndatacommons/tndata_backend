from business_rules.actions import BaseActions, rule_action
from business_rules.variables import BaseVariables
from business_rules.variables import (
    string_rule_variable
)
from rules.rulesets import ModelRuleset
from . models import Action, Behavior, Goal

# NOTE: After createing a ModelRulset subclass, you need to register it in the
# AppConfig.ready method.

# TODO: Not sure how to really structure all of this; it seems these rules
# should be based on user inputs, so maybe creating Action/Behavior/Goal
# variables is not the correct approach.
#
# IDEA: Actions based on when a user has `completed` an Action?
# Action:  send a well-done notification?

# --- Goal Rules --------------------------------------------------------------


class GoalVariables(BaseVariables):
    """Exposes a `Goal`'s data as business-rules variables."""
    def __init__(self, goal):
        self.goal = goal

    @string_rule_variable()
    def title(self):
        return self.goal.title


class GoalActions(BaseActions):
    def __init__(self, goal):
        self.goal = goal

    # TODO: Figure out what *real* actions we need.
    @rule_action()
    def similar_goals(self):
        qs = Goal.objects.exclude(id=self.goal.id)
        qs = qs.filter(categories__in=self.goal.categories.all())
        print("Similar Goals: {0}".format(g.title for g in qs))


class GoalRuleset(ModelRuleset):
    model = Goal
    variables = GoalVariables
    actions = GoalActions
    stop_on_first_trigger = False


# --- Behavior Rules ----------------------------------------------------------

class BehaviorVariables(BaseVariables):

    def __init__(self, behavior):
        self.behavior = behavior

    @string_rule_variable()
    def title(self):
        return self.behavior.title


class BehaviorActions(BaseActions):
    def __init__(self, behavior):
        self.behavior = behavior

    # TODO: Figure out what *real* actions we need.
    @rule_action()
    def similar_behaviors(self):
        qs = Behavior.objects.exclude(id=self.behavior.id)
        qs = qs.filter(categories__in=self.behavior.categories.all())
        print("Similar Behaviors: {0}".format(b.title for b in qs))


class BehaviorRuleset(ModelRuleset):
    model = Behavior
    variables = BehaviorVariables
    actions = BehaviorActions
    stop_on_first_trigger = False


# --- Action Rules ----------------------------------------------------------

class ActionVariables(BaseVariables):

    def __init__(self, action):
        self.action = action

    @string_rule_variable()
    def title(self):
        return self.action.title


class ActionActions(BaseActions):
    def __init__(self, action):
        self.action = action

    # TODO: Figure out what *real* actions we need.
    @rule_action()
    def similar_actions(self):
        qs = Action.objects.exclude(id=self.action.id)
        qs = qs.filter(categories__in=self.action.categories.all())
        print("Similar Actions: {0}".format(b.title for b in qs))


class ActionRuleset(ModelRuleset):
    model = Action
    variables = ActionVariables
    actions = ActionActions
    stop_on_first_trigger = False
