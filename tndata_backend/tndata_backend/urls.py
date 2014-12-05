from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from rest_framework import routers
from rest_framework.authtoken import views as rf_auth_views

from diary.api import EntryViewSet
from userprofile.api import UserViewSet, UserProfileViewSet


# Routers provide an eaasy way of automatically determining the URL conf
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'userprofiles', UserProfileViewSet)
router.register(r'diary/entries', EntryViewSet)


urlpatterns = patterns('',
    # TODO: override the ObtainAuthToken view class to customize what's returned, here?
    url(r'^api/token-auth/', rf_auth_views.obtain_auth_token),
    url(r'^api/', include(router.urls)),
    url(
        r'^api-auth/',
        include('rest_framework.urls',
        namespace='rest_framework')
    ),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name="index.html")),
)
