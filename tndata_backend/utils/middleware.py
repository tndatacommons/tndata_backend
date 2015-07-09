import pytz

from django.utils import timezone

TZ_SESSION_KEY = "django_timezone"


class TimezoneMiddleware(object):
    """Simple middleware that set's the user's timezone."""

    def _get_user_timezone(self, request):
        # If a TZ is stored in a session, use it...
        tzname = request.session.get(TZ_SESSION_KEY, None)
        if tzname is None:
            # Otherwise, look up the user's tz info
            try:
                if request.user.is_authenticated():
                    tzname = request.user.userprofile.timezone
                    request.session[TZ_SESSION_KEY] = tzname
            except pytz.UnknownTimeZoneError:
                pass
        return tzname

    def process_request(self, request):
        tzname = self._get_user_timezone(request)
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
