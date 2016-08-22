from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from utils.user_utils import local_day_range


class Command(BaseCommand):
    """Users should only have a single DailyProgress instance, per day. This
    command will delete duplicates, but only for *today*.

    """
    help = "Removes users' duplicate DailyProgress objects for today"

    def handle(self, *args, **options):
        User = get_user_model()
        for u in User.objects.all():
            today = local_day_range(u)
            progresses = u.dailyprogress_set.filter(created_on__range=today)
            if progresses.count() > 1:
                msg = "{} has duplicate DailyProgresses.\n"
                self.stdout.write(msg.format(u.email))
                count = 0
                for dp in progresses[1:]:
                    dp.delete()
                    count += 1
                self.stdout.write("- deleted {}\n".format(count))
