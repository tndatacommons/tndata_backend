from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import BaseThrottle


class BrowsableAPIRendererWithoutForms(BrowsableAPIRenderer):

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        ctx['display_edit_forms'] = False
        return ctx


class NoThrottle(BaseThrottle):
    """A throttling class to use for testing DRF api endpoints."""
    def allow_request(self, request, view):
        return True
