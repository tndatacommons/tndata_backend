import logging
import requests
import waffle

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from goals.sequence import get_next_useractions_in_sequence
from utils.user_utils import to_utc


logger = logging.getLogger(__name__)


if settings.DEBUG:
    FB_MESSENGER_URL = 'https://brad.ngrok.io/send/{user_id}'
else:
    FB_MESSENGER_URL = 'https://compass-fb-messenger.herokuapp.com/send/{user_id}'


# -----------------------------------------------------------------------------
#
# NOTICE:
#
# This script will likely send a message to a user every time it is run, so
# don't schedule it to run too quickly.
#
# -----------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Sends messages to our FB messenger users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            action='store',
            dest='user',
            default=None,
            help=("Restrict this command to the given User. "
                  "Accepts a username, email, or id")
        )

    def _get_users(self, options):
        User = get_user_model()

        # Check to see if we're just running this for a specific user
        if options.get('user', False):
            user = options['user']
            try:
                if user.isnumeric():
                    criteria = Q(id=user)
                else:
                    criteria = (Q(username=user) | Q(email=user))
                # Return an iterable, but use .get() to raise an exception
                # if there's not matching user.
                user = User.objects.get(criteria)
                return [user]
            except User.DoesNotExist:
                raise CommandError("Could not find user: {0}".format(user))

        # Find all the users that no email, no GCM devices and only 16-digit usernames.
        return User.objects.filter(
            email='',
            username__regex=r'\d{16}',
            gcmdevice__isnull=True
        ).distinct()

    def send(self, user_id, message, useraction_id):
        payload = {'message': message, 'id': useraction_id}
        requests.post(FB_MESSENGER_URL.format(user_id=user_id), payload)
        self.stdout.write("Sent to {}: {}".format(user_id, message))

    def handle(self, *args, **options):
        # This switch allows us to completely disable creation of notifications
        if not waffle.switch_is_active('goals-fb-messenger'):
            return None

        now = timezone.now()

        # XXX: Assume we're all in central time, don't send at night.
        if now.hour < 12 or now.hour > 23:
            self.stderr.write("not running during evening/early morning")
            return None

        users = self._get_users(options)
        self.stdout.write("Found {} users".format(len(users)))

        for user in users:
            # Only support Sequenced Goals, Actions
            for ua in get_next_useractions_in_sequence(user):
                # Retrive the `next_reminder`, which will be in the
                # user's timezone, and may have been created weeks or
                # months ago. This is slightly different from other
                # UserActions, because we don't re-generate
                # these on the fly
                deliver_on = to_utc(ua.next_reminder)

                if deliver_on < now:
                    text = "{} {}".format(
                        ua.get_notification_text(),
                        ua.action.description
                    )
                    self.send(user.username, text, ua.id)
                    break  # only send 1 message.
