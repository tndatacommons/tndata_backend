from haystack import indexes
from goals.models import Action, Behavior, Category, Goal

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

    def get_model(self):
        return Category

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published(packaged_content=False)


class BehaviorIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all published Behavior."""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    url = indexes.CharField(model_attr='get_absolute_url')
    updated_on = indexes.DateTimeField(model_attr='updated_on')

    def get_model(self):
        return Behavior

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()


class ActionIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all published Actions."""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    url = indexes.CharField(model_attr='get_absolute_url')
    updated_on = indexes.DateTimeField(model_attr='updated_on')

    def get_model(self):
        return Action

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()
