from collections import Counter, OrderedDict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils import timezone

from goals.models import UserCompletedAction
from notifications.models import GCMDevice, GCMMessage
from userprofile.models import UserProfile
from utils.dateutils import date_range


def _zero_fill_time_series(time_dict, days):
    """Given a iterable of time series data (e.g. a dictionary of the form
    `{date: value}`), we'll zero-fill any values with missing dates, and
    return an ordered iterable of the form:

        [(date, value), ... ]

    """
    now = timezone.now()
    results = OrderedDict()
    for x in range(0, days):
        x = (now - timedelta(days=x)).strftime("%Y-%m-%d")
        results[x] = time_dict.get(x, 0)
    return list(reversed(list(results.items())))


@user_passes_test(lambda u: u.is_authenticated() and u.is_staff)
def index(request):
    # Some other things we (may) want:
    # - Messages per user per day
    # - Messages per user “got it” per day
    # - Sessions/day and month
    # - Time in app (by feed access, actionactivity) Note: measure if folks
    #   read the message
    # - Average session duration (in the app?)
    # - Portfolio of client interests by population and demographic
    # - We should be able to filter by population/organization

    days = 30  # how much history to display?

    User = get_user_model()
    now = timezone.now()
    since = now - timedelta(days=days)

    # New Users over the past few days, excluding @tndata folks
    signups = User.objects.filter(date_joined__gte=since)
    signups = signups.exclude(email__icontains='tndata.org')
    signups = signups.values_list('date_joined', flat=True)
    signups = Counter([d.strftime("%Y-%m-%d") for d in signups])
    signups = _zero_fill_time_series(signups, days)

    # Active Users based on userprofile.updated_on (since every login to the app
    # updates the userprofile).
    logins = {}
    for dt in [1, 7, 30, 60, 90]:
        login_date = now - timedelta(days=dt)
        logins[dt] = UserProfile.objects.filter(updated_on__gte=login_date).count()

    # > 90 days == 91
    ninety = now - timedelta(days=91)
    logins[91] = UserProfile.objects.filter(updated_on__gte=ninety).count()

    # Active Devices (and misc stats)
    total_devices = GCMDevice.objects.all().count()
    device_owners = len(set(GCMDevice.objects.values_list("user", flat=True)))
    devices_per_user = total_devices / device_owners
    devices = GCMDevice.objects.values_list('device_type', flat=True)
    devices = Counter(list(devices))

    # Notification interactions
    ucas = UserCompletedAction.objects.filter(created_on__gte=since)
    completed = ucas.filter(state=UserCompletedAction.COMPLETED)
    completed = completed.values_list("created_on", flat=True)
    completed = Counter([d.strftime("%Y-%m-%d") for d in completed])
    completed = _zero_fill_time_series(completed, days)

    dismissed = ucas.filter(state=UserCompletedAction.DISMISSED)
    dismissed = dismissed.values_list("created_on", flat=True)
    dismissed = Counter([d.strftime("%Y-%m-%d") for d in dismissed])
    dismissed = _zero_fill_time_series(dismissed, days)

    # Notification Numbers
    messages = GCMMessage.objects.filter(deliver_on__range=date_range(now))
    messages_total = messages.count()
    messages_delivered = messages.filter(success=True).count()
    messages_remaining = messages_total - messages_delivered

    # Notification Preferences
    max_messages = Counter(list(UserProfile.objects.values_list(
        'maximum_daily_notifications', flat=True)))

    context = {
        'days': days,
        'total_users': User.objects.all().count(),
        'signups': signups,
        'logins': logins,
        'total_devices': total_devices,
        'device_owners': device_owners,
        'devices_per_user': devices_per_user,
        'devices': devices,
        'completed': completed,
        'dismissed': dismissed,
        'messages_total': messages_total,
        'messages_delivered': messages_delivered,
        'messages_remaining': messages_remaining,
        'max_messages': dict(max_messages),
    }
    return render(request, 'dashboard/index.html', context)
