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
        r'new/behavior/$',
        views.BehaviorCreateView.as_view(),
        name='behavior-create'
    ),
    url(
        r'new/action/$',
        views.ActionCreateView.as_view(),
        name='action-create'
    ),
    url(
        r'new/upload/$',
        views.upload_csv,
        name='upload-csv'
    ),

    # Actions
    url(
        r'actions/$',
        views.ActionListView.as_view(),
        name='action-list'
    ),
    url(
        r'action/(?P<title_slug>.+)/update/$',
        views.ActionUpdateView.as_view(),
        name='action-update'
    ),
    url(
        r'action/(?P<title_slug>.+)/delete/$',
        views.ActionDeleteView.as_view(),
        name='action-delete'
    ),
    url(
        r'action/(?P<title_slug>.+)/$',
        views.ActionDetailView.as_view(),
        name='action-detail'
    ),

    # Behaviors
    url(
        r'behaviors/$',
        views.BehaviorListView.as_view(),
        name='behavior-list'
    ),
    url(
        r'behavior/(?P<title_slug>.+)/update/$',
        views.BehaviorUpdateView.as_view(),
        name='behavior-update'
    ),
    url(
        r'behavior/(?P<title_slug>.+)/delete/$',
        views.BehaviorDeleteView.as_view(),
        name='behavior-delete'
    ),
    url(
        r'behavior/(?P<title_slug>.+)/$',
        views.BehaviorDetailView.as_view(),
        name='behavior-detail'
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
