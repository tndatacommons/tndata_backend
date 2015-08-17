"""
This is a sandbox for generateing dates and testing the results of
triggers; it's faster than running unit tests and lets me see a chunk of
dates all at once.

"""
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
    #rule = 'EXRULE:FREQ=WEEKLY;BYDAY=FR'  # every day but friday?

    # M, W, Th on Aug 17, 19, 20
    #rule = 'RRULE:FREQ=WEEKLY;UNTIL=20150820T050000Z;BYDAY=MO,WE,TH'
    #rule = 'RRULE:FREQ=WEEKLY;UNTIL=20150821T050000Z;BYDAY=MO,WE,TH'

    # Stacked:
    # Every Monday.
    # Every Tuesday until 8/15/2015 (sat)
    rule = (
        'RRULE:FREQ=WEEKLY;BYDAY=MO\n'
        'RRULE:FREQ=WEEKLY;UNTIL=20150815T050000Z;BYDAY=TU'
    )

    #     August 2015
    # Mo Tu We Th Fr Sa Su
    #                 1  2
    #  3  4  5  6  7  8  9
    # 10 11 12 13 14 15 16
    # 17 18 19 20 21 22 23
    # 24 25 26 27 28 29 30
    # 31

    START_DAY = 1  # Day of month to start on.
    NUM_DAYS = 20  # Number of days to test.
    Trigger.objects.filter(name="---testing this---").delete()
    t = Trigger.objects.create(
        name="---testing this---",
        trigger_type="time",
        time=time(9, 0),  # 9am
        #trigger_date=date(2015, 8, 1),
        #time=time(13, 0),  # 1pm
        #trigger_date=date(2015, 8, 10),  # 8/17/2015
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

    for i in range(NUM_DAYS):
        day = START_DAY + i
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
