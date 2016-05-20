from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^report/$',
        views.report,
        name='report'
    ),
    url(
        r'^remove-app-data/$',
        views.admin_remove_app_data,
        name='remove-app-data'
    ),
    url(
        r'^(?P<pk>\d+)/update/$',
        views.update_profile,
        name='update'
    ),
    url(
        r'^(?P<pk>\d+)/$',
        views.UserProfileDetailView.as_view(),
        name='detail'
    ),
    url(
        r'^$',
        views.UserProfileRedirectView.as_view(),
        name='index'
    ),
]
