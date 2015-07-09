from django.conf.urls import url
from . import views


urlpatterns = [
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
