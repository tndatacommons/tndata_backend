"""
This is a sandbox for generateing dates and testing the results of
triggers; it's faster than running unit tests and lets me see a chunk of
dates all at once.

"""
import re

from datetime import date, datetime, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone

from goals.models import Action, Category, Trigger


def parse_notification_text(action=None):
    # Update all the library's content, parsing the date/teim from the
    # notification_text, and including an updated dateteim string in the
    # external_resource field (and changeing external_resource_name)

    if action is None:
        cat = Category.objects.get(pk=44)  # Explore Memphis...
        actions = Action.objects.filter(behavior__goals__categories=cat)
        actions = actions.distinct()
        print("Found: {} Actions".format(actions.count()))
    else:
        actions = [action]

    count = 0
    for action in actions:
        # WAT! Some of these have a year of 2015
        if '2015, ' in action.notification_text:
            action.notification_text = action.notification_text.replace("2015, ", '')
        # Possible notification patterns
        # July 26, 10:15 am
        # June 10, 10 am
        patterns = [
            ('full', r'[A-Z][a-z]+ \d+, \d+:\d+ *[am|pm]*'),
            ('hours-only', r'[A-Z][a-z]+ \d+, \d+ *[am|pm]*'),
        ]
        matched = False  # did any of the patterns match?
        for name, pattern in patterns:
            match = re.search(pattern, action.notification_text)
            if match:
                # include the current year & convert to a datetime.
                datestring = match.group().replace(',', ', 2016')

                datefmt = '%B %d, %Y %I:%M %p'
                if name == 'hours-only':
                    datefmt = '%B %d, %Y %I %p'

                try:
                    date = datetime.strptime(datestring, datefmt)
                    # print("'{}' -> {} (using format '{}')".format(
                        # datestring, date, datefmt))

                    action.external_resource_name = "Add to calendar"
                    action.external_resource = date.strftime("%Y-%m-%d %H:%M:00")
                    action.save()
                    count += 1
                    matched = True
                    break;  # dont try any other patterns.
                except:
                    print("FAIL: action={}, '{}', with format: '{}'".format(
                        action.id, datestring, datefmt))

        if not matched:
            print("NO MATCH: {}".format(action.notification_text))
            # THESE were not supposed to be part of the library?
#            extraneous = [
#                'You can do this!',
#                'What does success look like?',
#                'Why do you want this?',
#                'You’re awesome!',
#                'Be proud of yourself!',
#                "What's in it for you?",
#                "How will you do it?",
#                "Think how you'll feel.",
#                "Sometimes life gets in the way.",
#                "Keep going!",
#                "How will you do this today?",
#                "Why do you want it?",
#                "Be committed.",
#                "What got in the way?",
#                "It’s a process.",
#                "One step at a time.",
#                "Make some time for this today.",
#                "You've got this.",
#                "Look how far you've come!",
#            ]
#            if action.notification_text in extraneous:
#                action.delete()
    print("Updated {}.".format(count))


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


def debug_useraction_dates(useraction):
    """Given a UserAction object, lets' print out all the various ways it
    may generate a notification date."""

    def _tf(dt):
        return dt.strftime("%a %x %X %Z") if dt else 'None'

    useraction.save()  # updates some of the item's time fields.

    # key = field/method that generates the date
    # value = tuple of (datetime, expected_timezone)
    attrs = {
        "next_trigger_date": (_tf(useraction.next_trigger_date), "UTC"),
        "next_reminder": (_tf(useraction.next_reminder), "local"),
        "next()": (_tf(useraction.next()), "local"),
        "_set_next_trigger_date()": (_tf(useraction._set_next_trigger_date()), "UTC"),
        "trigger.next(user=self.user)": (_tf(useraction.trigger.next(user=useraction.user)), "local"),
    }

    print("-" * 78)
    print("{: <28s} | {: <25s} | Expected Timzone".format("Method", "Result"))
    print("-" * 78)
    for attr, results in attrs.items():
        dt, expected_tz = results
        print("{: <28s} | {: <25s} | {}".format(attr, dt, expected_tz))


def sample_trigger_times(useraction, number=100):

    times = [useraction.trigger.dynamic_trigger_date(user=useraction.user) for n in range(number)]
    print("Hours: {}".format(set([t.hour for t in times])))

    return times


def teen_np():
    User = get_user_model()
    user = User.objects.get(username='bkmontgomery')
    actions = Action.objects.filter(
        behavior__goals__categories__id=35,
        default_trigger__frequency='monthly'
    )

    now = timezone.now()

    with patch("goals.models.triggers.timezone.now") as now:
        # Early morning
        now.return_value = tzdt(2016, 4, 15, 7, 0)

        for action in actions:
            t = action.default_trigger.next(user=user)
            delta = t - now()
            print("{}, {} days & {} hours from now".format(
                t.strftime("%c"), delta.days, int(delta.seconds / 3600)))

