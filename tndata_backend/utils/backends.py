"""
Custom Authentication Backends.

"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


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
        except User.DoesNotExist:
            pass

        return None
