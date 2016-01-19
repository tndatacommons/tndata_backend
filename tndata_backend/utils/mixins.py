from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache


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

    ----

    Versioned Docs (via docstrings)

    This mixin also makes use of DRF's self-describing API feature, but provides
    a method to include different docs for different versions of the api.

    To enable this, a `get_docstring` method will look for a `docstring_prefix`
    attribute which should be a directory containing your documentation. The
    convention is that your doc is the viewset's name, lowercased, with the
    version number tacked on the end; in a markdown file with a .md extension.

    For example: `UserViewSet`'s documentation for version 2 should be in a
    file named `userviewset_v2.md`. And if `docstring_prefix = "api_docs"`,
    this mixin will load the file (from your project root):

        api_docs/userviewset_v2.md

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

        # HACK: Dynamically write a new docstring based on the api version
        # It really makes little sense to do this work here, but this is
        # the appropriate part of this object's lifecycle to hook into this.
        docstring = self.get_docstring()
        if docstring:
            self.__class__.__doc__ = docstring
        return serializer_class

    def get_docstring(self):
        """Dynamically load a markdown file based on the api version; its
        content gets cached forever."""
        docstring = None
        docstring_prefix = getattr(self, 'docstring_prefix', None)
        if docstring_prefix:
            try:
                doc_file = "{}/{}_v{}.md".format(
                    docstring_prefix,
                    self.__class__.__name__.lower(),
                    self.request.version
                )
                docstring = cache.get(doc_file)
                if docstring is None:
                    docstring = open(doc_file).read()
                    cache.set(doc_file, docstring, timeout=None)
            except FileNotFoundError:
                pass
        return docstring
