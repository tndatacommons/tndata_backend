from unittest.mock import patch, Mock
from goals.models import Trigger
from datetime import date, datetime, time
from django.utils import timezone

def print_triggers():

    Trigger.objects.filter(name="---testing this---").delete()

    # every other day starting friday at 5pm
    t = Trigger.objects.create(
        name="---testing this---",
        trigger_type="time",
        time=time(13, 30),
        trigger_date=date(2015, 8, 12),
        recurrences='RRULE:FREQ=DAILY;INTERVAL=2'
    )
    #t.get_tz = Mock(return_value=pytz.timezone("America/Chicago"))
    print("Trigger Info:")
    print("- time: {0}".format(t.time))
    print("- date: {0}".format(t.trigger_date))
    print("- recr: {0}".format(t.serialized_recurrences()))
    print("---------------------------------------")
    for i in range(6):
        day = 12 + i
        with patch("goals.models.timezone.now") as now:
            d = timezone.make_aware(
                datetime(2015, 8, day, 13, 30), timezone=timezone.utc
            )
            now.return_value = d
            now_string = d.strftime("%a %x %X %Z")

            next_time = t.next()
            next_string = next_time.strftime("%a %x %X %Z")

            print("Now: {0}, Next: {1}".format(now_string, next_string))
    t.delete()
