import pytz
import time

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from redis_metrics import gauge, metric
from redis_metrics.utils import get_r

TZ_SESSION_KEY = "django_timezone"


class APIMetricsMiddleware:
    """Middleware to track metrics for our api.

    Currently tracked are:

    - endpoint usage: we just count how many times an endpoint is requested
    - response time: this is a gauge that gets updated on every request
      with an average response time.

    """
    def _current_average_response_time(self):
        # Assume `_start_time` and `_end_time` are set, retrieve the current
        # gauge value (if any), average the current response time, and return
        # the value (as a string).

        r = get_r()
        request_time = self._end_time - self._start_time

        current = r.get_gauge(self._key)
        if current is not None:
            current = (float(current) + request_time) / 2
        else:
            current = request_time
        return current

    def process_request(self, request):
        self._key = None

        # ONLY track api usage.
        if request.path.startswith("/api/"):
            self._start_time = time.time()
            self._key = request.path.strip('/').replace('/', '-')

    def process_response(self, request, response):
        if self._key:
            # Capture the ending time and update our gauge
            self._end_time = time.time()

            # Set the gauge
            gauge(self._key, self._current_average_response_time())

            # Inspect the original response to see which endpoint was called
            metric(self._key, category="API Metrics")

        return response


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


class ResponseForbiddenMiddleware(object):
    """Renders the 403.html template for all explicitely returned 403 responses.

    e.g. when a view returns HttpResponseForbidden()

    This middleware excludes the response from django's built-in
    'permission_denied' view.

    """
    def process_response(self, request, response):
        # Only check if there's a 404 for the original response
        if response.status_code != 403:
            return response

        if '<html' in response.content.decode("utf8"):
            # This is the result of the 'permission_denied' view, which has
            # alread rendered the 403.html template, so just return it.
            return response

        # all other explicit 403s
        ctx = {"message": response.content}
        return render(request, "403.html", ctx, status=response.status_code)


class IgnoreRequestMiddleware(object):
    """Sometimes we get obviously bad requests. If we can detect those, we'll
    just ignore them outright, returning a little easer egg instead.

    To test this, set DEBUG=False, and use:

         curl --verbose --header 'Host: example.com' 'http://yoursite.com'

    NOTE: In order for this to work, this must be listed first in the
    MIDDLEWARE_CLASSES setting.

    """
    def _ignore_domain(self, request):
        """ignore requests from obviously bad domains. This will circumvent
        those annoying Invalid HTTP_HOST header errors."""
        ignored_domains = getattr(settings, 'IGNORE_BAD_HOST_HEADERS', [])
        return any([
            domain in request.META.get('HTTP_HOST', '')
            for domain in ignored_domains
        ])

    def process_request(self, request):
        if self._ignore_domain(request):
            teapot = """<html><body><pre>
                                   (
                        _           ) )
                     _,(_)._        ((
                ___,(_______).        )
              ,'__.   /       \    /\_
             /,' /  |""|       \  /  /
            | | |   |__|       |,'  /
             \`.|                  /
              `. :           :    /
                `.            :.,'
                  `-.________,-'

            </pre></body></html>"""
            resp = HttpResponse(teapot)
            resp.status_code = 418
            return resp


class DebugMedia404Middleware(object):
    """Catch media requests that return 404 and return an image instead."""

    def __init__(self, *args, **kwargs):
        # pre-load our default image & create a response
        with open("utils/static/img/x.png", 'rb') as f:
            self._fallback_response = HttpResponse(
                f.read(),
                content_type="image/png",
            )
            self._fallback_response.status_code = 200
        super().__init__(*args, **kwargs)

    def process_response(self, request, response):
        # Only check if there's a 404 for the original response
        media_request = request.path.startswith(settings.MEDIA_URL)
        if settings.DEBUG and media_request and response.status_code == 404:
                return self._fallback_response
        return response
