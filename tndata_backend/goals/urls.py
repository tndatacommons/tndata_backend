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
        r'new/interest/$',
        views.InterestCreateView.as_view(),
        name='interest-create'
    ),
    url(
        r'new/goal/$',
        views.GoalCreateView.as_view(),
        name='goal-create'
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
        r'action/(?P<name_slug>.+)/update/$',
        views.ActionUpdateView.as_view(),
        name='action-update'
    ),
    url(
        r'action/(?P<name_slug>.+)/delete/$',
        views.ActionDeleteView.as_view(),
        name='action-delete'
    ),
    url(
        r'action/(?P<name_slug>.+)/$',
        views.ActionDetailView.as_view(),
        name='action-detail'
    ),
    url(
        r'actions/$',
        views.ActionListView.as_view(),
        name='action-list'
    ),

    # Goals
    url(
        r'goal/(?P<name_slug>.+)/update/$',
        views.GoalUpdateView.as_view(),
        name='goal-update'
    ),
    url(
        r'goal/(?P<name_slug>.+)/delete/$',
        views.GoalDeleteView.as_view(),
        name='goal-delete'
    ),
    url(
        r'goal/(?P<name_slug>.+)/$',
        views.GoalDetailView.as_view(),
        name='goal-detail'
    ),
    url(
        r'goals/$',
        views.GoalListView.as_view(),
        name='goal-list'
    ),

    # Interests
    url(
        r'interest/(?P<name_slug>.+)/update/$',
        views.InterestUpdateView.as_view(),
        name='interest-update'
    ),
    url(
        r'interest/(?P<name_slug>.+)/delete/$',
        views.InterestDeleteView.as_view(),
        name='interest-delete'
    ),
    url(
        r'interest/(?P<name_slug>.+)/$',
        views.InterestDetailView.as_view(),
        name='interest-detail'
    ),
    url(
        r'interests/$',
        views.InterestListView.as_view(),
        name='interest-list'
    ),

    # Categories
    url(
        r'categories/$',
        views.CategoryListView.as_view(),
        name='category-list'
    ),
    url(
        r'category/(?P<name_slug>.+)/update/$',
        views.CategoryUpdateView.as_view(),
        name='category-update'
    ),
    url(
        r'category/(?P<name_slug>.+)/delete/$',
        views.CategoryDeleteView.as_view(),
        name='category-delete'
    ),
    url(
        r'category/(?P<name_slug>.+)/$',
        views.CategoryDetailView.as_view(),
        name='category-detail'
    ),
)
