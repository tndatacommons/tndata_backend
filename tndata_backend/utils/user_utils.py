import hashlib
import pytz

from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from django.utils import timezone


def get_client_ip(request):
    """Try to get the user's client IP address, and return it.

    See: http://stackoverflow.com/a/4581997/182778

    NOTE: This function attemps to pull the IP address from
    HTTP_X_FORWARDED_FOR, but falls back to the REMOTE_ADDR value.

    It uses the first item in X-Forwarded-For, but we may want to use the
    last item (esp. if we were on something like Heroku). From the django docs:
    "relying on REMOTE_ADDR or similar values is widely known to be a worst
    practice".

    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def user_timezone(user, timeout=3600):
    """Return the user's timezone (as specified on their UserProfile).

    This function is heavily cached, because accessing `user.userprofile.timezone`
    spawns a database query, and when this is done for each item in a list
    of serialized objects, it may result in 100s of unnessary queries.

    Returns a string containing the user's timezone, e.g. "America/Chicago"

    """
    key = "usertz-{}".format(user.id)
    tz = cache.get(key)
    if tz is None:
        try:
            tz = user.userprofile.timezone
        except ObjectDoesNotExist:
            tz = "America/Chicago"
        cache.set(key, tz, timeout)
    return tz


def tzdt(*args, **kwargs):
    """Return a timezone-aware datetime object."""
    tz = kwargs.pop("tz", timezone.utc)
    dt = datetime(*args)
    return timezone.make_aware(dt, timezone=tz)


def to_utc(dt):
    """Convert the given naive/aware datetime to UTC."""
    if dt and timezone.is_aware(dt):
        dt = dt.astimezone(timezone.utc)
    elif dt:
        dt = timezone.make_aware(dt, timezone.utc)
    return dt


def to_localtime(dt, user):
    """Given a datetime object, convert it to the user's localtime.

    * dt - either a naive or aware datetime object. If naive, the user's
      timezone will be applied, making it aware. If aware, the datetime object
      will be converted to the user's timezone.
    * user - a User instance. They must have a UserProfile with a set timezone
      for this to work properly.

    """
    tz = user_timezone(user)
    if dt and tz:
        tz = pytz.timezone(tz)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone=tz)
        else:
            dt = dt.astimezone(tz)
    return dt


def local_now(user):
    """Return a `now` time in the user's local timezone."""
    now = timezone.now()
    return to_localtime(now, user)


def local_day_range(user, dt=None, days=None):
    """Return a tuple of the form (start, end), containing datetime objects
    in utc time that represents the range for the user's full day.

    * user: a User instance. The User whom we're considering.
    * dt: (optional). If given, this is the datetime around which the range
      is constructed.
    * days = (optional) Number of days over which the range should spread. The
      default behavior is for the range to encompass a single day.

    This is useful to query for objects that were updated or created during the
    user's day; e.g.

        Model.objects.filter(created__range=local_day_range(user))

    """
    if dt is None:
        dt = local_now(user)
    else:
        dt = to_localtime(dt, user)

    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    if days:
        end = end + timedelta(days=days)
    return (start.astimezone(timezone.utc), end.astimezone(timezone.utc))


def get_all_permissions(user, sort=False):
    """Given a user, this returns a list of all Permission objects, that are
    either assigned to the user or assigned to one of the user's Groups.

    * user: a User instance
    * sort: Sort the list (default is False)

    """
    permissions = list(user.user_permissions.all())
    for group in user.groups.all():
        for perm in group.permissions.all():
            permissions.append(perm)
    if sort:
        permissions = sorted(permissions, key=lambda p: p.name)
    return permissions


def date_hash():
    """Generate an MD5 hash based on the current time."""
    return hashlib.md5(datetime.now().strftime("%c").encode("utf8")).hexdigest()


def hash_value(input_string):
    """Given some input string, hash it with md5 and return a hexdigest"""
    m = hashlib.md5()
    m.update(input_string.encode("utf8"))
    return m.hexdigest()


def username_hash(email, max_length=30):
    """Generates a Username hash from an email address."""
    return hash_value(email.strip().lower())[:max_length]


def create_inactive_user(email):
    """Creates a user account that's marked as inactive and needing onboarding.

    If this is given an email address for an existing user, that user is returned
    instead of creating a new user.

    """
    User = get_user_model()
    email = email.strip().lower()
    try:
        return User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        pass

    username = username_hash(email)
    user = User.objects.create_user(username, email)
    user.is_active = False
    user.set_unusable_password()
    user.save()
    try:
        user.userprofile.set_needs_onboarding()
    except ObjectDoesNotExist:
        from userprofile.models import UserProfile
        UserProfile.objects.create(user=user, needs_onboarding=True)
    return user
