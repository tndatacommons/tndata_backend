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
