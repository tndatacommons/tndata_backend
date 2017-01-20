import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chat.models import ChatMessage
from chat.utils import generate_room_name


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Converts ChatMessage room names so they're based on User.id instead "
        "of User.username"
    )

    def handle(self, *args, **options):
        User = get_user_model()

        for msg in ChatMessage.objects.all():
            username_a, username_b = msg.room.split('-')[1:]
            try:
                user_a = User.objects.get(username=username_a)
                user_b = User.objects.get(username=username_b)

                msg.room = generate_room_name((user_a, user_b))
                msg.save()
            except (User.DoesNotExist, ValueError):
                err = "Could not find users for room: {}".format(msg.room)
                self.stdout.write(err)
                logger.info(err)
