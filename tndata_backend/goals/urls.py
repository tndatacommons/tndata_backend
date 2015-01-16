from django.conf.urls import patterns, include, url
from . import views


urlpatterns = patterns('',
    url(
        r'^$',
        views.CategoryList.as_view(),
        name='index'
    ),
    url(
        r'(?P<name_slug>.+)/$',
        views.CategoryDetailView.as_view(),
        name='category-detail'
    ),
)
