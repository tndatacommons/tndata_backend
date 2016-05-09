from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from goals.models import Action, Behavior, Trigger


# This command will save the IDs for all of the created actions, so if (for
# some reason) we need to kill them we can.
OUTPUT_FILE = '/var/tmp/duplicated_actions.txt'


class Command(BaseCommand):
    """Use this command to copy Action objects form one or more models
    into ALL *published* behaviors. This command accepts IDs and a flag that
    tells us whether or not the parent object is a Category, Goal, or Behavior.

    Example Usage:

    - Copy Actions from Behaviors with ID = 43, 44 into ALL published Behaviors:

        ./manage.py duplicate_actions_into_behaviors 43 44

    - Copy Actions from the Goal with ID = 42 into ALL published Behaviors:

        ./manage.py duplicate_actions_into_behaviors --goal 42

    - Copy Actions from the Categories with IDs = 1, 2, 3 into ALL published
      Behaviors:

        ./manage.py duplicate_actions_into_behaviors --cateogry 1 2 3

    - Additionally, we can exclude some Behaviors from having Actions copied
      into them, e.g.: Copy Actions from Behaviors with ID = 5, 6 into all
      published Behaviors EXCEPT for those with ID = 7, 9

        ./manage.py duplicate_actions_into_behaviors 5, 6 --exclude 7 9


    """
    help = 'Creates duplicate Actions in ALL Behaviors'

    def add_arguments(self, parser):
        parser.add_argument('object_id', nargs='+', type=int)
        parser.add_argument(
            "-c",
            "--category",
            dest='category',
            action="store_true",
            default=False,
            help="Is the specified object ID a Category?"
        )
        parser.add_argument(
            "-g",
            "--goal",
            dest='goal',
            action="store_true",
            default=False,
            help="Is the specified object ID a Goal?"
        )
        parser.add_argument(
            "-b",
            "--behavior",
            dest='behavior',
            action="store_true",
            default=True,
            help="Is the specified object ID a Behavior (this is the default)?"
        )
        parser.add_argument(
            "-e",
            "--exclude",
            dest='exlude_behaviors',
            nargs='*',
            action="store",
            default=None,
            type=int,
            help="IDs for behaviors that should be excluded when creating actions"
        )

    def _get_actions(self, options):
        # Given an object id and some options that tell us what kind of
        # object it is, we want to find a queryset of actions beneath it. These
        # are the actions we'll duplicate into *every* Behavior.
        try:
            object_ids = options['object_id']
        except (TypeError, ValueError):
            raise CommandError("{} are not a valid database ids".format(
                options['object_id']))

        criteria = {}
        if options.get('category'):
            criteria['behavior__goals__categories__pk__in'] = object_ids
        elif options.get('goal'):
            criteria['behavior__goals__pk__in'] = object_ids
        elif options.get('behavior'):
            criteria['behavior__pk__in'] = object_ids
        else:
            raise CommandError(
                'You must specify an object type with -g, -c, or -b')

        actions = Action.objects.filter(**criteria).distinct()

        # Exclude any behaviors that were specified
        excluded = options.get('exclude_behaviors', None)
        if excluded:
            actions = actions.exclude(behavior__pk__in=excluded)

        return actions

    def _copy_trigger(self, old_trigger):
        return Trigger.objects.create(
            time_of_day=old_trigger.time_of_day,
            frequency=old_trigger.frequency,
            time=old_trigger.time,
            trigger_date=old_trigger.trigger_date,
            recurrences=old_trigger.recurrences,
            start_when_selected=old_trigger.start_when_selected,
            stop_on_complete=old_trigger.stop_on_complete,
            disabled=old_trigger.disabled,
            relative_value=old_trigger.relative_value,
            relative_units=old_trigger.relative_units
        )

    def _copy_action(self, action, behavior, trigger, state='published'):
        action = Action.objects.create(
            title=action.title,
            behavior=behavior,  # New Parent Behavior
            action_type=action.action_type,
            sequence_order=action.sequence_order,
            source_link=action.source_link,
            source_notes=action.source_notes,
            notes=action.notes,
            more_info=action.more_info,
            description=action.description,
            external_resource=action.external_resource,
            external_resource_name=action.external_resource_name,
            notification_text=action.notification_text,
            icon=action.icon,  # NOTE: Links to existing icon on S3
            state=state,  # Changed.
            priority=action.priority,
            bucket=action.bucket,
            default_trigger=trigger,  # our new trigger above.
            updated_by=action.updated_by,
            created_by=action.created_by,
        )
        # Save the ID to the output file.
        self._output_file.write("{},".format(action.id))
        return action

    def handle(self, *args, **options):
        self._output_file = open(OUTPUT_FILE, "w")
        new_action_count = 0
        new_trigger_count = 0

        # Actions that we want to copy
        actions = self._get_actions(options)

        try:
            # All-or-nothing: If any of this fails,
            # we will back out of the transaction.
            with transaction.atomic():

                # For every behavior, bulk-create copies of the above actions.
                for behavior in Behavior.objects.all():
                    for action in actions:
                        # Don't create duplicate content.
                        lookup = behavior.action_set.filter(title=action.title)
                        if not lookup.exists():
                            trigger = self._copy_trigger(action.default_trigger)
                            new_trigger_count += 1

                            self._copy_action(action, behavior, trigger)
                            new_action_count += 1

                msg = "Created {} new Actions and {} new Triggers"
                self.stdout.write(msg.format(new_action_count, new_trigger_count))

            self._output_file.close()
            msg = "IDs for new actions written to: {}"
            self.stdout.write(msg.format(OUTPUT_FILE))

        except IntegrityError as e:
            # Remove all the stuff written to our outputfile.
            self.output_file.seek(0)
            self.output_file.truncate()
            self._output_file.close()

            # Now raise an exception w/ our error.
            err = "Exception encountered: '{}'; transaction rolled back"
            raise CommandError(err.format(e))
