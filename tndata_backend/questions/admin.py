from django.contrib import admin
from . import models


class ArrayFieldListFilter(admin.SimpleListFilter):
    """An admin list filter based on the values from a model's `keywords`
    ArrayField. For more info, see the django docs:

    https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter

    """
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Keywords"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'keywords'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        keywords = models.Question.objects.values_list("keywords", flat=True)
        keywords = [(kw, kw) for sublist in keywords for kw in sublist if kw]
        keywords = sorted(set(keywords))
        return keywords

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        lookup = self.value()
        if lookup:
            queryset = queryset.filter(keywords__contains=[lookup])
        return queryset



@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'votes', '_keywords', 'created_on',
    )
    list_filter = ('published', ArrayFieldListFilter, )
    search_fields = (
        'title', 'content',
        'user__email', 'user__first_name', 'user__last_name',
    )
    raw_id_fields = ('user', 'voters')

    def _keywords(self, obj):
        return ", ".join(sorted(kw for kw in obj.keywords if kw))


@admin.register(models.Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'teaser', 'votes', 'user', 'created_on')
    search_fields = (
        'question__content', 'content',
        'user__email', 'user__first_name', 'user__last_name',
    )
    raw_id_fields = ('question', 'user', 'voters')
