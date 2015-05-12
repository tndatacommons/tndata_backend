from django.core.management.base import BaseCommand

from goals.models import UserAction, UserBehavior
from notifications.models import GCMDevice, GCMMessage


class Command(BaseCommand):
    help = 'Creates notification Messages for users Actions & Behaviors'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages_created = 0

    def create_message(self, user, obj, title, message, delivery_date):
        if delivery_date is None:
            self.stderr.write("{0} has no trigger date".format(obj))
        else:
            try:
                GCMMessage.objects.create(
                    user, obj, title, message, delivery_date
                )
                self._messages_created += 1
            except GCMDevice.DoesNotExist:
                msg = "User {0} has not registered a Device".format(user)
                self.stderr.write(msg)

    def handle(self, *args, **options):
        # Make sure everything is ok before we run this.
        self.check()

        # Schedule notifications for Behaviors
        for ub in UserBehavior.objects.all():
            self.create_message(
                ub.user,
                ub.behavior,
                ub.behavior.title,
                ub.behavior.notification_text,
                ub.behavior.get_trigger().next()
            )

        # Schedule notifications for Actions
        for ua in UserAction.objects.all():
            self.create_message(
                ua.user,
                ua.action,
                ua.action.title,
                ua.action.notification_text,
                ua.action.get_trigger().next()
            )

        # Finish with a confirmation message
        m = "Created {0} notification messages.".format(self._messages_created)
        self.stdout.write(m)
