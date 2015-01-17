from django.conf.urls import patterns, include, url
from . import views


urlpatterns = patterns('',
    url(
        r'^$',
        views.CategoryList.as_view(),
        name='index'
    ),

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

    # TODO: Crud for Actions

    # Crud for Interests
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

    # crud for Category
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
