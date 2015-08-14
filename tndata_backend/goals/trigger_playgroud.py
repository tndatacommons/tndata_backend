from unittest.mock import patch
from goals.models import Trigger
from datetime import date, datetime, time
from django.utils import timezone


def tzdt(*args, **kwargs):
    return timezone.make_aware(datetime(*args), timezone=timezone.utc)


def print_triggers():
    #rule='RRULE:FREQ=DAILY;INTERVAL=2'
    #rule = 'RRULE:FREQ=DAILY;UNTIL=20150815T050000Z'  # Daily until 8/15
    #rule = 'EXRULE:FREQ=WEEKLY;BYDAY=SA,SU'  # Weekly except Sat/Sun
    #rule = 'RRULE:FREQ=WEEKLY;BYDAY=SA,SU;COUNT=4'
    rule = 'EXRULE:FREQ=WEEKLY;BYDAY=FR'  # every day but friday?

    Trigger.objects.filter(name="---testing this---").delete()
    t = Trigger.objects.create(
        name="---testing this---",
        trigger_type="time",
        #trigger_date=date(2015, 8, 1),
        time=time(13, 0),
        recurrences=rule
    )
    print("Trigger Info:")
    print("- {0}".format(t.recurrences_as_text()))
    print("- time: {0}".format(t.time))
    print("- date: {0}".format(t.trigger_date))
    print("- recr: {0}".format(t.serialized_recurrences()))
    print("---------------------------------------")

    # Time format
    tf = "%a %x %X %Z"
    tf = "%c %Z"

    #     August 2015
    # Mo Tu We Th Fr Sa Su
    #                 1  2
    #  3  4  5  6  7  8  9
    # 10 11 12 13 14 15 16
    # 17 18 19 20 21 22 23
    # 24 25 26 27 28 29 30
    # 31

    for i in range(7):
        day = 13 + i
        with patch("goals.models.timezone.now") as now:
            # Early morning
            now.return_value = tzdt(2015, 8, day, 6, 0)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))

            # Late morning
            now.return_value = tzdt(2015, 8, day, 11, 0)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))

            # Afternoon
            now.return_value = tzdt(2015, 8, day, 13, 30)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))
        print("------------------------------------")
    t.delete()
