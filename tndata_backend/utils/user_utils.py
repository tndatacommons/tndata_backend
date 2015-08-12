import hashlib
from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist


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
