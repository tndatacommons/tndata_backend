from django.conf.urls import patterns, include, url
from django.contrib import admin

from rest_framework import routers
from userprofile.api import UserViewSet


# Routers provide an eaasy way of automatically determining the URL conf
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)


urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    url(
        r'^api-auth/',
        include('rest_framework.urls',
        namespace='rest_framework')
    ),
    url(r'^admin/', include(admin.site.urls)),
)
