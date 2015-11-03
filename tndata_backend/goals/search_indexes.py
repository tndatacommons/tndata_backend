from haystack import indexes
from goals.models import Action, Behavior, Category, Goal


class CategoryIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all public, non-packaged Categories."""
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='updated_on')

    def get_model(self):
        return Category

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published(packaged_content=False)


class GoalIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all public, non-packaged Goals."""
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='updated_on')

    def get_model(self):
        return Goal

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()


class BehaviorIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all published Behavior."""
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='updated_on')

    def get_model(self):
        return Behavior

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()


class ActionIndex(indexes.SearchIndex, indexes.Indexable):
    """A search index for all published Actions."""
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='updated_on')

    def get_model(self):
        return Action

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()
