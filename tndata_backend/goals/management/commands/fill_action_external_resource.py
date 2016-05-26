from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from goals.models import Action, Category


class Command(BaseCommand):
    help = "Currently fills an Action's external_resource / external_resource_name fields with a trigger time"

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            action='store',
            dest='category',
            default=None,
            help="Restrict this command to a Category (pk or title). "
        )

    def _get_category(self, category):
        try:
            if category and category.isnumeric():
                return Category.objects.get(pk=category)
            elif category:
                return Category.objects.get(title__iexact=category)
            else:
                raise Category.DoesNotExist
        except Category.DoesNotExist:
            raise CommandError("Could not find Category: {}".format(category))

    def handle(self, *args, **options):

        total = 0
        updated = 0
        category = self._get_category(options['category'])

        actions = Action.objects.filter(behavior__goals__categories=category)
        for action in actions.distinct():
            # Only change this if it's empty.
            time = action.default_trigger.time
            date = action.default_trigger.trigger_date
            if time and date and not action.external_resource.strip():
                # combine the time & date into a tz-unaware datetime string
                dt = datetime.combine(date, time).strftime("%Y-%m-%d %H:%M:%S")
                action.external_resource = dt
                action.external_resource_name = "datetime"
                action.save()
                updated += 1
            total += 1

        self.stdout.write("Updated {} (of {}) Actions\n".format(updated, total))
