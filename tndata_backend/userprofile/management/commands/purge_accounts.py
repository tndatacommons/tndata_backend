from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q


class Command(BaseCommand):

    help = 'Purges user accounts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help="Remove a user's messages. Accepts a username, email, or id"
        )

    def handle(self, *args, **options):
        # XXX: this command should only be used in staging/debug
        if not (settings.DEBUG or settings.STAGING):
            raise CommandError("This command is not available in production")

        # Users whose emails look like this will not be deleted.
        keepers = ['example.com', 'tndata.org', ]

        User = get_user_model()
        users = User.objects.all()
        for domain in keepers:
            users = users.exclude(email__endswith=domain)

        # See if we're trying to purge an individual
        if options['user']:
            try:
                if options['user'].isnumeric():
                    criteria = Q(id=options['user'])
                else:
                    criteria = (
                        Q(username=options['user']) | Q(email=options['user'])
                    )

                users = [users.get(criteria)]
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(options['user'])
                raise CommandError(msg)

        # Related object types that we'll delete first.
        object_types = [
            'customgoal',
            'customaction',
            'usercompletedcustomaction',
            'customactionfeedback',
            'useraction',
            'usergoal',
            'usercategory',
            'trigger',
            'usercompletedaction',
            'dailyprogress',
            'packageenrollment',
            'gcmmessage',
        ]

        count = 0
        for user in users:
            for ot in object_types:
                # e.g. call: user.useraction_set.all().delete()
                attr = "{}_set".format(ot)
                getattr(user, attr).all().delete()

            # Clear some other relations
            user.categories_updated.clear()
            user.categories_created.clear()
            user.goals_updated.clear()
            user.goals_created.clear()
            user.actions_created.clear()
            user.actions_updated.clear()

            # then delete the user
            user.delete()
            count += 1

        self.stdout.write("Removed {} user accounts.\n".format(count))
