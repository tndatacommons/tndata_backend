from datetime import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from notifications.models import GCMMessage

logger = logging.getLogger("loggly_logs")


class Command(BaseCommand):
    help = 'Removes messages that have already been delivered'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help="Remove a user's messages. Accepts a username, email, or id"
        )

        parser.add_argument(
            '--before',
            action='store',
            dest='before_date',
            default=None,
            help="Remove all messages scheduled before the given date "
                 "(in YYYY-mm-dd format)"
        )

        parser.add_argument(
            '--after',
            action='store',
            dest='after_date',
            default=None,
            help="Remove all messages scheduled after the given date "
                 "(in YYYY-mm-dd format)"
        )

        parser.add_argument(
            '--all',
            action='store_true',
            dest='remove_all',
            default=False,
            help="Remove all messages"
        )

    def _delete(self, queryset):
        """Calls delete on a queryset, and logs the appropriate message."""
        if queryset.exists():
            msg = "Expired {0} GCM Messages".format(queryset.count())
            queryset.delete()  # Delete those expired messages.
            logger.info(msg)

    def _parse_date(self, datestring):
        try:
            return datetime.strptime(datestring, '%Y-%m-%d')
        except ValueError:
            msg = '"{}" is not a valid date format (YYYY-mm-dd)'.format(datestring)
            raise CommandError(msg)

    def handle(self, *args, **options):

        if options['user']:
            # If given a user, remove all of the user's messages.

            User = get_user_model()
            try:
                if options['user'].isnumeric():
                    criteria = Q(id=options['user'])
                else:
                    criteria = (
                        Q(username=options['user']) | Q(email=options['user'])
                    )
                user = User.objects.get(criteria)
                qs = GCMMessage.objects.filter(user=user)
                self._delete(qs)
            except User.DoesNotExist:
                msg = "Could not find user: {0}".format(options['user'])
                raise CommandError(msg)

        elif options['before_date']:
            # Remove all GCMMessages scheduled before the give date.
            dt = self._parse_date(options['before_date'])
            qs = GCMMessage.objects.filter(deliver_on__lte=dt)
            self._delete(qs)

        elif options['after_date']:
            # Remove all GCMMessages scheduled after the give date.
            dt = self._parse_date(options['after_date'])
            qs = GCMMessage.objects.filter(deliver_on__gte=dt)
            self._delete(qs)

        elif options['remove_all']:
            # Remove all GCMMessages.
            self._delete(GCMMessage.objects.all())

        else:
            # Default action: Remove all expired messages.
            qs = GCMMessage.objects.expired()
            self._delete(qs)
