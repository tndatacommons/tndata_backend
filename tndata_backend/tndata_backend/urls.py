from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import login, logout
from django.views.generic import TemplateView

from rest_framework import routers

from goals.api import (
    BehaviorSequenceViewSet,
    BehaviorActionViewSet,
    CategoryViewSet,
    GoalViewSet,
    TriggerViewSet,
)
from userprofile.api import UserViewSet, UserProfileViewSet, obtain_auth_token


class IndexView(TemplateView):
    """TODO: you have to sublcass TemplateView to provide extra context.
    this should probably go somewhere else.
    """
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        if not self.request.user.is_authenticated():
            context['login_form'] = AuthenticationForm()
        return context


# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()

# ViewSets from the goals app.
router.register(r'categories', CategoryViewSet)
router.register(r'goals', GoalViewSet)
router.register(r'triggers', TriggerViewSet)
router.register(r'sequences', BehaviorSequenceViewSet)
router.register(r'actions', BehaviorActionViewSet)

# ViewSets from the userprofile app.
router.register(r'users', UserViewSet)
router.register(r'userprofiles', UserProfileViewSet)


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
    url(r'^goals/', include('goals.urls', namespace='goals')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, {'next_page': '/'}, name="logout"),
    url(r'^$', IndexView.as_view())
)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
