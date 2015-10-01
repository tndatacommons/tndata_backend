from django.core.cache import cache
from functools import wraps


def cached_method(cache_key):
    """Cache a method, using it's first argument to set a cache key.

    Params:

    * cache_key is a format string used to set a cache key, e.g. "{}-foo"

    Usage:

        class SomeThing:
            @cached_method("{}-key")
            def get_stuff(self, obj):
                # ...

    In the amove `get_stuff` method, obj.id will be used to generate the cache
    key. NOTE: this was intended to be used on serializer methods.

    """
    def decorate(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 1:  # extract the first arg & use as the cache key
                key = cache_key.format(args[1])
                result = cache.get(key)
                if result is None:
                    result = func(*args, **kwargs)
                    cache.set(key, result)
                return result
            # Nothing to use as a cache key, just call the method.
            return func(*args, **kwargs)
        return wrapper
    return decorate
