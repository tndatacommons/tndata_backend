from contextlib import ContextDecorator
from functools import wraps
from time import time

from django.conf import settings
from django.core.cache import cache


def cached_method(cache_key, timeout=settings.CACHE_TIMEOUT):
    """Cache a method, using the ID attribute of it's first argument to set
    a cache key. NOTE: If this first argument for the cached method doesn't
    have an ID attribute, nothing will happen.

    Params:

    * cache_key is a format string used to set a cache key, e.g. "{}-foo"

    Usage:

        class SomeThing:
            @cached_method("{}-key")
            def get_stuff(self, obj):
                # ...

    In the above `get_stuff` method, `obj.id` will be used to generate the
    cache key. NOTE: this was intended to be used on serializer methods.

    """
    def decorate(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 1:
                # extract the first objected passed into the function & use
                # its id attribute as part of the cache key
                cache_object = args[1]
                if not hasattr(cache_object, 'id'):
                    return None  # just bail if there's no ID.

                key = cache_key.format(cache_object.id)
                result = cache.get(key)
                if result is None:
                    result = func(*args, **kwargs)
                    cache.set(key, result, timeout=timeout)
                return result
            # Nothing to use as a cache key, just call the method.
            return func(*args, **kwargs)
        return wrapper
    return decorate


class timed(ContextDecorator):
    """A simple context manager / decorator that captures execution time.

    Usage:

        with timed():
            # do some stuff

    Or as a decorator:

        @timed()
        def func():
            # ...

    You can also pass in an `output` callable that will be passed the elasped
    time. For example, with `print`:

        @timed(output=print)
        def func():
            # ...

        func() -> print(elapsed)

    """
    def __init__(self, *args, **kwargs):
        self.output = kwargs.pop('output', None)
        super().__init__(*args, **kwargs)

    def __enter__(self):
        self.start = time()
        return self

    def __exit__(self, type, value, traceback):
        self.end = time()
        self.elapsed = self.end - self.start
        if self.output is not None:
            self.output(self.elapsed)
