from django.conf import settings
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    """A mixin for a class-based view that requires the user to be logged in.

    Borrowed from: https://goo.gl/CtYx3s

    """

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


# API ViewSet mixins
# ------------------

class VersionedViewSetMixin:
    """This mixin adds a api version lookup to a viewset. For this to work,
    include this mixin on your ViewSet class, and set a `serializer_class_vX`
    attribute, e.g.:

        serializer_class_v1 = serializers.v1.FooSerializer
        serializer_class_v2 = serializers.v2.FooSerializer

    If for some reason the class does not include the appropriate serializer
    class attribute, the default version will be returned.

    """
    # Mapping of version number to local, expected attribute name
    _versions = {
        '1': 'serializer_class_v1',
        '2': 'serializer_class_v2',
    }

    def get_serializer_class(self):
        try:
            attr_name = self._versions[self.request.version]
            serializer_class = getattr(self, attr_name)
        except (KeyError, AttributeError):
            default = settings.REST_FRAMEWORK['DEFAULT_VERSION']
            attr_name = "serializer_class_v{}".format(default)
            serializer_class = getattr(self, attr_name)

        return serializer_class
