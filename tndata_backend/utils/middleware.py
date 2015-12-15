import pytz
from django.http import HttpResponse
from django.shortcuts import render
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
    just ignore them outright.

        Referrer: http://bradmontgomery.net/installation/CHANGELOG
        Requested URL: /installation/CHANGELOG
        User agent: Go 1.1 package http
        IP address: 142.54.184.181

    Let's give them a little gift.

    """
    IGNORE_DOMAINS = [   # List of HTTP_HOST header domains we'll just ignore
        'proxyradar.com',
    ]

    def _ignore_domain(self, request):
        """ignore requests from obviously bad domains. This will circumvent
        those annoying Invalid HTTP_HOST header errors."""
        return any([
            domain in request.META.get('HTTP_HOST', '')
            for domain in self.IGNORE_DOMAINS
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
