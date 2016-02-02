from rest_framework import exceptions
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import BaseThrottle
from rest_framework.versioning import QueryParameterVersioning


class DefaultQueryParamVersioning(QueryParameterVersioning):
    """This class includes the default version into requests that do not
    specify a version.

    NOTE: this should be fixed in DRF 3.3.3 whenever it's released:
    https://github.com/tomchristie/django-rest-framework/pull/3833

    """
    def determine_version(self, request, *args, **kwargs):
        version = request.query_params.get(
            self.version_param,
            self.default_version,
        )
        if not self.is_allowed_version(version):
            raise exceptions.NotFound(self.invalid_version_message)
        return version


class BrowsableAPIRendererWithoutForms(BrowsableAPIRenderer):
    # NOTE: the template for the browesable api is:
    # template = 'rest_framework/api.html'

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        ctx['display_edit_forms'] = False
        return ctx


class NoThrottle(BaseThrottle):
    """A throttling class to use for testing DRF api endpoints."""
    def allow_request(self, request, view):
        return True
