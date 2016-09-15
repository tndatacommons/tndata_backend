from redis_metrics import metric
from rest_framework import viewsets
from . import models
from . import serializers


class FunContentViewSet(viewsets.ReadOnlyModelViewSet):
    """This is a read-only endpoint that serves various types of _fun content_,
    including:

    * Inspirational or Famous Quotes (quote)
    * Fortune Cookies (fortune)
    * Fun Facts (fact)
    * Jokes (joke)

    ## Fields

    Each item in the results array contains the following fields:

    * `id` -- a unique ID for the object
    * `message_type` -- the type of content: quote|fortune|fact|joke
    * `message` -- the main text of the content
    * `author` -- the autor or an attribution if any
    * `keywords` -- an array of keywords relevant for the content (if any)

    ## Filtering

    You can filter this list using the following querystring parameters:

    * `?type={message_type}`, e.g. ?type=joke for jokes.
    * `?author={name_or_partial}`, e.g. attempt to filter based on author. e.g.
      `?author=roosevelt` would return content for Eleanor, Franklin D, and Theodore
    * `?keywords={keywords}` would return all items that contain the given keyword
    * `?random=1` would return a single, random result

    You can include multiple filters to narrow results. For example,
    `?type=quote&author=milne&random=1` would return a random quote from AA Milne.

    """
    queryset = models.FunContent.objects.all()
    serializer_class = serializers.FunContentSerializer

    def get_queryset(self):
        message_type = self.request.GET.get('type', None)
        author = self.request.GET.get('author', None)
        keywords = self.request.GET.getlist('keywords', [])
        random = self.request.GET.get('random', False)

        # Track metrics on the number of random reward content objects requested
        if random:
            metric('viewed-random-reward', category="Rewards")
            return [models.FunContent.objects.random()]

        queryset = super().get_queryset()
        if message_type is not None:
            queryset = queryset.filter(message_type=message_type)

        if author is not None:
            queryset = queryset.filter(author__icontains=author)

        if keywords:
            queryset = queryset.filter(keywords__contains=keywords)

        return queryset
