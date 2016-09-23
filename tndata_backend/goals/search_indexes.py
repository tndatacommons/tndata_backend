import json
from haystack import indexes
from goals.models import Action, Category, Goal

# -----------------------------------------------------------------------------
# NOTE on haystack fields; see https://goo.gl/1S79dX
#
# - text is used by convention, and is the blob of text (read from a template)
#   that gets indexed.
# - id, django_ct, django_id & content are reserved for use by haystack
# - Stored Fields can help prevent DB access when displaying results, e.g.
#   title, description, etc.
# -----------------------------------------------------------------------------


class GoalIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all public, non-packaged Goals, AND all child Action
    content.

    The GoalIndex index is a special case, in that it contains more text than
    that available from the Goal model.For the mobile app, the api only
    exposes the GoalIndex for users to search. It therefore contains both
    Goal content and Action content.

    """
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    url = indexes.CharField(model_attr='get_absolute_url')
    updated_on = indexes.DateTimeField(model_attr='updated_on')
    serialized_object = indexes.CharField()  # Serialized object details.

    def prepare_serialized_object(self, obj):
        # This sucks; serializers import models, as do indexes, but serializers
        # also import the index, so we've got a circular dependency.
        from goals.serializers import v2
        return json.dumps(v2.GoalSerializer(obj).data)

    def get_model(self):
        return Goal

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()


class CategoryIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all public, non-packaged Categories."""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    url = indexes.CharField(model_attr='get_absolute_url')
    updated_on = indexes.DateTimeField(model_attr='updated_on')
    serialized_object = indexes.CharField()  # Serialized object details.

    def prepare_serialized_object(self, obj):
        # This sucks; serializers import models, as do indexes, but serializers
        # also import the index, so we've got a circular dependency.
        from goals.serializers import v2
        return json.dumps(v2.CategorySerializer(obj).data)

    def get_model(self):
        return Category

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published(packaged_content=False)


class ActionIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all published Actions."""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    url = indexes.CharField(model_attr='get_absolute_url')
    updated_on = indexes.DateTimeField(model_attr='updated_on')
    serialized_object = indexes.CharField()  # Serialized object details.

    def prepare_serialized_object(self, obj):
        # This sucks; serializers import models, as do indexes, but serializers
        # also import the index, so we've got a circular dependency.
        from goals.serializers import v2
        return json.dumps(v2.ActionSerializer(obj).data)

    def get_model(self):
        return Action

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()
