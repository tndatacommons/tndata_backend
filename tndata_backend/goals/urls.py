from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),

    # Create views
    url(
        r'new/category/$',
        views.CategoryCreateView.as_view(),
        name='category-create'
    ),
    url(
        r'new/trigger/$',
        views.TriggerCreateView.as_view(),
        name='trigger-create'
    ),
    url(
        r'new/goal/$',
        views.GoalCreateView.as_view(),
        name='goal-create'
    ),
    url(
        r'new/behaviorsequence/$',
        views.BehaviorSequenceCreateView.as_view(),
        name='behaviorsequence-create'
    ),
    url(
        r'new/behavioraction/$',
        views.BehaviorActionCreateView.as_view(),
        name='behavioraction-create'
    ),
    url(
        r'new/upload/$',
        views.upload_csv,
        name='upload-csv'
    ),

    # Behavior Actions
    url(
        r'behavioractions/$',
        views.BehaviorActionListView.as_view(),
        name='behavioraction-list'
    ),
    url(
        r'behavioraction/(?P<name_slug>.+)/update/$',
        views.BehaviorActionUpdateView.as_view(),
        name='behavioraction-update'
    ),
    url(
        r'behavioraction/(?P<name_slug>.+)/delete/$',
        views.BehaviorActionDeleteView.as_view(),
        name='behavioraction-delete'
    ),
    url(
        r'behavioraction/(?P<name_slug>.+)/$',
        views.BehaviorActionDetailView.as_view(),
        name='behavioraction-detail'
    ),

    # Behavior Sequences
    url(
        r'behaviorsequences/$',
        views.BehaviorSequenceListView.as_view(),
        name='behaviorsequence-list'
    ),
    url(
        r'behaviorsequence/(?P<name_slug>.+)/update/$',
        views.BehaviorSequenceUpdateView.as_view(),
        name='behaviorsequence-update'
    ),
    url(
        r'behaviorsequence/(?P<name_slug>.+)/delete/$',
        views.BehaviorSequenceDeleteView.as_view(),
        name='behaviorsequence-delete'
    ),
    url(
        r'behaviorsequence/(?P<name_slug>.+)/$',
        views.BehaviorSequenceDetailView.as_view(),
        name='behaviorsequence-detail'
    ),

    # Triggers
    url(
        r'triggers/$',
        views.TriggerListView.as_view(),
        name='trigger-list'
    ),
    url(
        r'trigger/(?P<name_slug>.+)/update/$',
        views.TriggerUpdateView.as_view(),
        name='trigger-update'
    ),
    url(
        r'trigger/(?P<name_slug>.+)/delete/$',
        views.TriggerDeleteView.as_view(),
        name='trigger-delete'
    ),
    url(
        r'trigger/(?P<name_slug>.+)/$',
        views.TriggerDetailView.as_view(),
        name='trigger-detail'
    ),

    # Goals
    url(
        r'goal/(?P<title_slug>.+)/update/$',
        views.GoalUpdateView.as_view(),
        name='goal-update'
    ),
    url(
        r'goal/(?P<title_slug>.+)/delete/$',
        views.GoalDeleteView.as_view(),
        name='goal-delete'
    ),
    url(
        r'goal/(?P<title_slug>.+)/$',
        views.GoalDetailView.as_view(),
        name='goal-detail'
    ),
    url(
        r'goals/$',
        views.GoalListView.as_view(),
        name='goal-list'
    ),

    # Categories
    url(
        r'categories/$',
        views.CategoryListView.as_view(),
        name='category-list'
    ),
    url(
        r'category/(?P<title_slug>.+)/update/$',
        views.CategoryUpdateView.as_view(),
        name='category-update'
    ),
    url(
        r'category/(?P<title_slug>.+)/delete/$',
        views.CategoryDeleteView.as_view(),
        name='category-delete'
    ),
    url(
        r'category/(?P<title_slug>.+)/$',
        views.CategoryDetailView.as_view(),
        name='category-detail'
    ),
)
