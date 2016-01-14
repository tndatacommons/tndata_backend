from rest_framework import exceptions
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import BaseThrottle
from rest_framework.versioning import QueryParameterVersioning
from clog.clog import clog


class DefaultQueryParamVersioning(QueryParameterVersioning):
    """This class includes the default version into requests that do not
    specify a version."""
    def determine_version(self, request, *args, **kwargs):
        version = request.query_params.get(
            self.version_param,
            self.default_version,
        )
        clog(version, title="version in determine_version")

        if not self.is_allowed_version(version):
            raise exceptions.NotFound(self.invalid_version_message)
        return version


class BrowsableAPIRendererWithoutForms(BrowsableAPIRenderer):

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        ctx['display_edit_forms'] = False
        return ctx


class NoThrottle(BaseThrottle):
    """A throttling class to use for testing DRF api endpoints."""
    def allow_request(self, request, view):
        return True
