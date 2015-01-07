from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from rest_framework import routers

from diary.api import EntryViewSet
from goals.api import (
    ActionViewSet,
    ActionTakenViewSet,
    CategoryViewSet,
    InterestViewSet,
    CustomReminderViewSet,
    SelectedActionViewSet,
)
from userprofile.api import UserViewSet, UserProfileViewSet, obtain_auth_token


# Routers provide an eaasy way of automatically determining the URL conf
router = routers.DefaultRouter()
router.register(r'actions', ActionViewSet)
router.register(r'actions_taken', ActionTakenViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'interests', InterestViewSet)
router.register(r'selected_actions', SelectedActionViewSet)
router.register(r'reminders', CustomReminderViewSet)
router.register(r'users', UserViewSet)
router.register(r'userprofiles', UserProfileViewSet)
router.register(r'diary/entries', EntryViewSet)


urlpatterns = patterns('',
    url(r'^api/token-auth/', obtain_auth_token),
    url(r'^api/', include(router.urls)),
    url(
        r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    url(
        r'^rules/',
        include('rules.urls', namespace='rules')
    ),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name="index.html")),
)
