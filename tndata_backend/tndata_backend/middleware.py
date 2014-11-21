import os
import re

from django.http import Http404, HttpResponse
from django.conf import settings


class PolymerDevMiddleware(object):
    """Middleware that'll let Django's development server serve Polymer files.

    How this works: Any time there's a 404 request, this middleware will scan
    the TEMPLATE_DIRS and STATICFILES_DIRS directories to see if there are any
    matching files.

    This should only be used, when:

        * doing local development
        * DEBUG=True

    For production, you should let a real webserver (nginx or apache) serve
    your Polymer components.

    """

    def _read_file(self, requested_path):
        """Attempt to read the requested file from disk."""
        dirs = settings.TEMPLATE_DIRS + settings.STATICFILES_DIRS
        for p in dirs:
            path = os.path.join(p, requested_path)
            if os.path.exists(path):
                return open(path).read()
        raise Http404

    def process_response(self, request, response):
        # Return immediately if we have a response or we're not in DEBUG mode.
        if not settings.DEBUG or response.status_code != 404:
            return response

        try:
            content = self._read_file(request.path.strip("/"))
            return HttpResponse(content)
        except Http404:
            # Always return 404 responses as-is
            return response
        except:
            # Raise any exceptions in DEBUG mode, else pass the response along
            if settings.DEBUG:
                raise
            return response
