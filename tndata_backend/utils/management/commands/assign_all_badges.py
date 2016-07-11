from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from badgify.models import Badge, Award


class Command(BaseCommand):
    help = 'Awards ALL Badges to the specified user'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('user', nargs=1, type=str)

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = options['user'][0]

            if user.isnumeric():
                criteria = Q(id=user)
            else:
                criteria = (Q(username=user) | Q(email=user))
            user = User.objects.get(criteria)

            # Award every badge to the given user (except for those already awarded)
            badges = Award.objects.filter(user=user).values_list('badge', flat=True)
            badges = Badge.objects.exclude(pk__in=badges)
            Award.objects.bulk_create([
                Award(badge=badge, user=user) for badge in badges
            ])
            self.stdout.write("Badges have been awared to {}\n".format(user))

        except (IndexError, User.DoesNotExist):
            raise CommandError('Could not find the specified user')
