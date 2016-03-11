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


def time_only_triggers():
    # Triggers with a time, but NO date and NO recurrences.
    triggers = Trigger.objects.filter(
        time__isnull=False,
        trigger_date__isnull=True,
        recurrences__isnull=True
    )
    print("Found {}...".format(triggers.count()))
    results = []
    for t in triggers:
        user_actions = t.useraction_set.all()
        if user_actions.count() > 1:
            ua_id = "x"
            action_id = "x"
            action = "MULTIPLE"
        else:
            ua = user_actions.first()
            ua_id = ua.id
            action_id = ua.action.id
            action = ua.action.title

        # 0 - Trigger id
        # 1 - user email
        # 2 - action id
        # 3 - useraction id
        # 4 - action title
        # 5 - trigger time
        # 6 - trigger next
        results.append(
            (t.id, t.user.email[:16], action_id, ua_id, action[:35], t.time, t.next())

        )

    results = sorted(results, key=lambda l: l[5])
    for result in results:
        print("{0:5}) {1:16} / ({2:4}/{3:4}) {4:35} -- [{5}] {6}".format(*result))

    return triggers


def _print_trigger(trigger):
    print("Trigger Info:")
    print("- {0}".format(trigger.recurrences_as_text()))
    print("- time: {0}".format(trigger.time))
    print("- date: {0}".format(trigger.trigger_date))
    print("- recr: {0}".format(trigger.serialized_recurrences()))
    print("- user: {0}".format(trigger.user))
    print("- name: {0}".format(trigger.name))
    print("- start when selected? {}".format(trigger.start_when_selected))
    print("- stop on complete? {}".format(trigger.stop_on_complete))
    print("- relative? {} {}".format(trigger.relative_value, trigger.relative_units))
    print("---------------------------------------")


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

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(pk=1)

    START_DAY = 1  # Day of month to start on.
    NUM_DAYS = 10  # Number of days to test.
    Trigger.objects.filter(name="---testing this---").delete()

    t = Trigger.objects.create(
        user=user,  # Make this a custom trigger
        name="testing",
        time=time(12, 0),  # 12:00 pm
        trigger_date=date(2016, 1, 6),
        #recurrences=rule
        start_when_selected=True,
        relative_value=5,
        relative_units='days'
    )
    _print_trigger(t)

    # Time format
    tf = "%a %x %X %Z"
    tf = "%c %Z"

    for i in range(NUM_DAYS):
        day = START_DAY + i
        with patch("goals.models.timezone.now") as now:
            # Early morning
            now.return_value = tzdt(2016, 1, day, 6, 0)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))

            # Late morning
            now.return_value = tzdt(2016, 1, day, 11, 0)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))

            # Afternoon
            now.return_value = tzdt(2016, 1, day, 13, 30)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))
        print("------------------------------------")
    t.delete()



def dynamic_triggers():

    # PRINT this calendar with: calendar.prmonth(2016, 3)
    # ---------------------------------------------------
    #      March 2016
    # Mo Tu We Th Fr Sa Su
    #     1  2  3  4  5  6
    #  7  8  9 10 11 12 13
    # 14 15 16 17 18 19 20
    # 21 22 23 24 25 26 27
    # 28 29 30 31

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(pk=1)

    YEAR = 2016
    MONTH = 3
    START_DAY = 1  # Day of month to start on.
    NUM_DAYS = 10  # Number of days to test.

    Trigger.objects.filter(name="testing").delete()
    t = Trigger.objects.create(
        user=user,
        name="testing",
        frequency="weekly",
        time_of_day='noonish'
    )

    # Time format
    tf = "%a %x %X %Z"
    tf = "%c %Z"

    for i in range(NUM_DAYS):
        day = START_DAY + i
        with patch("goals.models.triggers.timezone.now") as now:
            # Early morning
            now.return_value = tzdt(YEAR, MONTH, day, 6, 0)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))

            # Late morning
            now.return_value = tzdt(YEAR, MONTH, day, 11, 0)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))

            # Afternoon
            now.return_value = tzdt(YEAR, MONTH, day, 13, 30)
            now_string = now().strftime(tf)
            next_time = t.next()
            next_string = next_time.strftime(tf) if next_time else "None"
            print("Now: {0} --> Next: {1}".format(now_string, next_string))
        print("------------------------------------")
    t.delete()
