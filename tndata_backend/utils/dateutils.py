from datetime import time
from django.utils import timezone


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
