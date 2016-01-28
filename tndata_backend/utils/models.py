"""
This app has no models, but some utility classes & functions for views are
defined here.

"""
from datetime import datetime
from hashlib import md5
from urllib.parse import urlsplit

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy
from django.template.loader import render_to_string


class ResetToken:
    """A session-based token for password resets."""

    token_key = "resettoken"  # temporary token to proove ownership
    email_key = "resetemail"  # email address of the user.
    expiry = 1800  # 30 minutes

    def __init__(self, request, email=None):
        self.request = request
        self.email = email
        self.token = None

    @staticmethod
    def check(request, token):
        """Checks the given token against the session key."""
        key = ResetToken.token_key
        return key in request.session and request.session[key] == token

    @staticmethod
    def delete(request):
        """Remove the current token from the session."""
        request.session.pop(ResetToken.token_key)
        request.session.pop(ResetToken.email_key)

    @staticmethod
    def get_email(request):
        return request.session.get(ResetToken.email_key, None)

    def generate(self):
        """Generates a token, saving it to the current session."""
        if self.email is None:
            raise ValueError(
                "You cannot generate a ResetToken without an email address"
            )
        t = "{0}|{1}".format(datetime.utcnow().strftime("%c"), self.email)
        self.token = md5(t.encode('utf8')).hexdigest()
        self.request.session[self.token_key] = self.token
        self.request.session[self.email_key] = self.email
        self.request.session.set_expiry(self.expiry)
        return self.token

    def send_email_notification(self):
        """Send an email with a link to the password reset form."""

        # Pull the FQDN from the referer
        url = self.request.META.get('HTTP_REFERER', None)
        if url is None:
            url = self.request.META.get('HTTP_HOST', None)
        if url is None:
            url = self.request.META.get('SERVER_NAME', None)
        if url is None:
            url = "https://app.tndata.org"
        path = reverse_lazy("utils:set_new_password", args=[self.token])

        url_data = urlsplit(url)
        base_url = "{0}://{1}".format(
            url_data.scheme or 'http',
            url_data.netloc or url_data.path
        )
        url = "{0}{1}".format(base_url, path)

        template = "utils/email/password_reset_notification.txt"
        context = {
            'token': self.token,
            'url': url,
            'base_url': base_url,
            'expiry': self.expiry / 60,
        }
        subject = "Password Reset"
        message = render_to_string(template, context)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False
        )
