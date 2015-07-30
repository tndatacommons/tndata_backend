import hashlib
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist


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
        pass
    return user
