from django.conf.urls import patterns, include, url
from . import views


urlpatterns = patterns('',
    url(
        r'^$',
        views.CategoryList.as_view(),
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
        r'new/action/$',
        views.ActionCreateView.as_view(),
        name='action-create'
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

    # Categories
    url(
        r'(?P<name_slug>.+)/update/$',
        views.CategoryUpdateView.as_view(),
        name='category-update'
    ),
    url(
        r'(?P<name_slug>.+)/delete/$',
        views.CategoryDeleteView.as_view(),
        name='category-delete'
    ),
    url(
        r'(?P<name_slug>.+)/$',
        views.CategoryDetailView.as_view(),
        name='category-detail'
    ),
)
