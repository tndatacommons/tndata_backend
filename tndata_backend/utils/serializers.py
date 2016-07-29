from collections import OrderedDict
from rest_framework import serializers


class ObjectTypeModelSerializer(serializers.ModelSerializer):
    object_type = serializers.SerializerMethodField()

    def get_object_type(self, obj):
        return obj.__class__.__name__.lower()


def resultset(iterable):
    """Given any iterable, wrap it in the meta data expected to create a dict
    result set, e.g.:

    Turn this:

        [{id: 1}, {id: 2}, ...]

    Into:

        {
            count: 5,
            next: null,
            prev: null,
            results: [
                {id: 1}, {id: 2}, ...
            ]
        }

    """
    results = OrderedDict(count=0, next=None, prev=None, results=list())
    results['count'] = len(iterable)
    results['results'] = list(iterable)
    return results
