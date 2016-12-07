"""
Custom Authentication Backends.

"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from utils.slack import post_message


class EmailAuthenticationBackend(ModelBackend):
    """Authenticate with email & password. This also works if a user supplies
    an email address in the username field."""

    def authenticate(self, username=None, email=None, password=None):
        User = get_user_model()

        # Support email addresses in the username field
        if email is None and username is not None:
            email = username

        try:
            user = User.objects.get(email__iexact=email)
            if user.check_password(password):
                return user
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email__iexact=email).latest('date_joined')
            # Fire off a notification about this
            if not settings.DEBUG and not settings.STAGING:
                err = ":warning: :bug: Duplicate account for user {}"
                post_message("#tech", err.format(user.email))

            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

        return None


class EmailAndTokenBackend(ModelBackend):
    """Authenticate with email and a api token."""

    def authenticate(self, email=None, token=None):
        User = get_user_model()

        try:
            return User.objects.get(email__iexact=email, auth_token__key=token)
        except (User.MultipleObjectsReturned, User.DoesNotExist):
            pass

        return None
