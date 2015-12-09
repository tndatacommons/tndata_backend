import hashlib
import pytz

from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from django.utils import timezone


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
    if dt and user.userprofile.timezone:
        tz = pytz.timezone(user.userprofile.timezone)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone=tz)
        else:
            dt = dt.astimezone(tz)
    return dt


def local_now(user):
    """Return a `now` time in the user's local timezone."""
    now = timezone.now()
    return to_localtime(now, user)


def local_day_range(user, dt=None):
    """Return a tuple of the form (start, end), containing datetime objects
    in utc time that represents the range for the user's full day.

    * user: a User instance. The User whom we're considering.
    * dt: (optional). If given, this is the datetime around which the range
      is constructed.

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


def username_hash(email, max_length=30):
    """Generates a Username hash from an email address."""
    m = hashlib.md5()
    m.update(email.encode("utf8"))
    return m.hexdigest()[:max_length]


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
