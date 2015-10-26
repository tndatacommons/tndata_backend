from datetime import time, timedelta
from django.utils import timezone

import pytz

from .user_utils import to_utc


def dates_range(num_days):
    """Return a generator that yields a datetime.date object for `num_days`
    in the past.

    """
    today = timezone.now()
    for d in range(num_days):
        yield today - timedelta(days=d)


def date_range(datetime_obj, tz=timezone.utc):
    """Return a range, `(start, end)`, tuple that spans the full day for the
    given datetime object.

    """
    start = datetime_obj.combine(datetime_obj, time.min)
    end = datetime_obj.combine(datetime_obj, time.max)

    if timezone.is_naive(start) and timezone.is_naive(end):
        start = timezone.make_aware(start, timezone=tz)
        end = timezone.make_aware(end, timezone=tz)

    return (start, end)


def print_utc_to_localtime(local="America/Chicago", tz=None):
    """Prints a UTC -> localtime table. Useful for wrapping your head around
    timezone issues.

    Arguments:

    * local -- the local timzone that you want information about. It must be
      a timzone string that is understood by pytz (e.g. America/Chicago)
    * tz -- optional: a timezone object to use as the local time (instead of
      the local keyword).

    """
    if tz is None and local:
        tz = pytz.timezone(local)

    s = "{} ---> {}"
    ltime = timezone.now().astimezone(tz)
    ltime = ltime.replace(hour=0, minute=0, second=0, microsecond=0)
    fmt = "%a %b %d, %H:%M %Z"  # Wed Oct 14, 15:00 CST
    for hour in range(0, 23):
        ltime = ltime.replace(hour=hour)
        utctime = to_utc(ltime)
        print(s.format(utctime.strftime(fmt), ltime.strftime(fmt)))
