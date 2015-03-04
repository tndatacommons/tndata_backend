from django.core.management.base import BaseCommand
from goals import models

import tablib


# A Mapping of models this script supports.
MODELS = {
    'category': models.Category,
    'interest': models.Interest,
    'goal': models.Goal,
    'trigger': models.Trigger,
    'behaviorsequence': models.BehaviorSequence,
    'behavioraction': models.BehaviorAction,
    'action': models.Action,
}


class Command(BaseCommand):
    args = '<modelname>'
    help = 'Exports data for a given model in a CSV file.'

    def _parse_args(self, args):
        try:
            return args[0].strip().lower()
        except (IndexError, ValueError):
            self.stderr.write("Error parsing input. Did you specify a model?")

    def _get_model(self, model_name):
        try:
            return MODELS[model_name]
        except KeyError:
            msg = "Unsupported model. Must be one of: {0}"
            self.stderr.write(msg.format([k for k in MODELS.keys()]))

    def handle(self, *args, **options):
        model_name = self._parse_args(args)
        Model = self._get_model(model_name)

        # HACK alert: dynamically generating all model fields.
        fields = [f.name for f in Model._meta.fields]
        data = tablib.Dataset([], headers=fields)

        for obj in Model.objects.all():
            data.append(getattr(obj, field) for field in fields)

        filename = "{0}.csv".format(model_name)
        with open(filename, "w") as f:
            f.write(data.csv)
        self.stdout.write("\nWrote CSV data to {0}\n".format(filename))
