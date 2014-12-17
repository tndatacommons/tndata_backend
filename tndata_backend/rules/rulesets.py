from collections import defaultdict

from business_rules import export_rule_data, run_all
from business_rules.actions import BaseActions
from business_rules.variables import BaseVariables


class ModelRuleset:
    """A Parent-class to encapsulate the defined Variables and Actions classes
    for a specific Django Model.

    USAGE: To use this, you'll need to do the following:

    1. Define your `BaseVariables` subclass to expose your model's variables.
    2. Define your `BaseActions` subclass to expose any actions you wish to allow.
    3. Then, define a subclass of `ModelRuleset`; This must have the following:
        * either a `model` or a `queryset` (if `model` only, queryset will
          be `model.objects.all()`.
        * variables: An attribute assigning your `BaseVariables` subclass.
        * actions: An attribute assigning your `BaseActions` subclass.
    4. Finally, register your `ModelRuleset` class.:

        ruleset.register('myapp', MyModelRuleset)

    Example:

        class EntryRuleset(ModelRuleset):
            model = Entry
            queryset = Entry.objects.all()
            variables = EntryVariables
            actions = EntryActions
            stop_on_first_trigger = False
        ruleset.register('blog', EntryRuleset)

    Done!

    """
    def __init__(self):
        self.stop_on_first_trigger = getattr(self, 'stop_on_first_trigger', True)
        try:
            qs = getattr(self, 'queryset', None)
            self.queryset = qs or self.model.objects.all()
            self.model = self.queryset.model
        except AttributeError:
            msg = (
                "Either model or queryset is a required attribute on all "
                "ModelRuleset subclasses."
            )
            raise AttributeError(msg)

        try:
            assert all([self.variables, self.actions])
        except AssertionError:
            msg = (
                "Both variables and actions attributes are required on all "
                "ModelRuleset subclasses."
            )
            raise AttributeError(msg)


class RuleSet:
    """This class encapsulates the set of rules for the project. A global
    instance of this will store references to all rules for a project.
    """
    def __init__(self):
        # app_name -> set(ModelRuleset instances, ...)
        self._registry = defaultdict(set)

    def register(self, app_name, obj):
        # Fail early if we don't pass these set of constraints.
        constraints = [
            issubclass(obj, ModelRuleset),
            issubclass(getattr(obj, 'variables', None), BaseVariables),
            issubclass(getattr(obj, 'actions', None), BaseActions),
        ]
        if not all(constraints):
            raise RuntimeError(
                "Failed to register RuleSet object(s). They must be subclasses "
                "ModelRuleset and contain valid variables and actions."
            )
        self._registry[app_name].add(obj)

    def export(self):
        """Expose all the registered rules' Variables and Actions."""
        export_data = defaultdict(list)
        for app_name, rulesets in self._registry.items():
            for ruleset in rulesets:
                model_name = ruleset.model.__name__.lower()
                rules = export_rule_data(ruleset.variables, ruleset.actions)
                key = "{0}_{1}".format(app_name, model_name)
                export_data[app_name].append(rules)
        return dict(export_data)

    def get_ruleset_rules(self, app_name, ruleset):
        """Given a ruleset (an instance of ModelRuleset), find all the rules
        that have been generated."""
        # TODO: query our model to save rules.
        # rulesets know:
        # -- model name (and queryset),
        # -- the app name
        pass

    def run(self):
        """Run all of the rules."""
        # NOTE: Presumably we'd do this for entries saved since some time period;
        # e.g. the last day, or the last 2 hours.
        #
        # TODO:^ build a management command to call this.
        for app_name, rulesets in self._registry.items():
            for ruleset in rulesets:
                for obj in ruleset.queryset:
                    run_all(
                        rule_list=self.get_ruleset_rules(app_name, ruleset),
                        defined_variables=ruleset.variables(obj),
                        defined_actions=ruleset.actions(obj),
                        stop_on_first_trigger=ruleset.stop_on_first_trigger
                    )

# The global registry of Rule Actions/Variables. Usage, e.g. in the foo app.
#
#   from rules.rulesets import ruleset
#   ruleset.register('foo', FooVariables)
#   ruleset.register('foo', FooActions)
ruleset = RuleSet()
