from django.core.management.base import BaseCommand
from goals.models import Action

import tablib


class Command(BaseCommand):
    """Exports a CSV file of titles for all public, published content. The
    content hierarchy is flattened into columns:

        Action, Behavior, Goals, Categories

    Cells with multiple items (e.g. goals) are separated by newlines.

    """
    help = 'Exports data for a given model in a CSV file.'

    def handle(self, *args, **options):

        headers = ['Action', 'Behavior', 'Goals', 'Categories']
        data = tablib.Dataset([], headers=headers)

        for action in Action.objects.published():

            # Action, Parent behavior
            row = [action.title, action.behavior.title]

            goals = []
            categories = []
            for goal in action.behavior.goals.published():
                goals.append(goal.title)
                for category in goal.categories.published():
                    categories.append(category.title)

            row.append("\n".join(goals))
            row.append("\n".join(categories))
            data.append(row)

        filename = "published_content_titles.csv"
        with open(filename, "w") as f:
            f.write(data.csv)
        self.stdout.write("\nWrote CSV data to {0}\n".format(filename))
