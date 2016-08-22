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

    def show_form_for_method(self, view, method, request, obj):
        return False

    def get_rendered_html_form(self, data, view, method, request):
        """
        Return a string representing a rendered HTML form, possibly bound to
        either the input or output data.

        In the absence of the View having an associated form then return None.

        See:

        https://github.com/tomchristie/django-rest-framework/blob/3.4.4/rest_framework/renderers.py#L438
        """
        return ""


class NoThrottle(BaseThrottle):
    """A throttling class to use for testing DRF api endpoints."""
    def allow_request(self, request, view):
        return True
