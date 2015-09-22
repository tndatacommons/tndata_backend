import hashlib
import pytz

from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from django.utils import timezone


def to_localtime(dt, user):
    """Given a datetime object, convert it to the user's localtime."""
    if user.userprofile.timezone:
        tz = pytz.timezone(user.userprofile.timezone)
        dt = timezone.make_naive(dt)
        dt = timezone.make_aware(dt, timezone=tz)
    return dt


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

    """
    User = get_user_model()

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
