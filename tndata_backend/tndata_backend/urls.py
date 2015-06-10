from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import login, logout
from django.views.generic import TemplateView

from rest_framework import routers

from goals.api import (
    ActionViewSet,
    BehaviorViewSet,
    BehaviorProgressViewSet,
    CategoryViewSet,
    CustomTriggerViewSet,
    GoalViewSet,
    TriggerViewSet,
    UserActionViewSet,
    UserBehaviorViewSet,
    UserCategoryViewSet,
    UserGoalViewSet,
)
from notifications.api import GCMDeviceViewSet, GCMMessageViewSet
from survey.api import (
    BinaryQuestionViewSet,
    BinaryResponseViewSet,
    InstrumentViewSet,
    LikertQuestionViewSet,
    LikertResponseViewSet,
    MultipleChoiceQuestionViewSet,
    MultipleChoiceResponseViewSet,
    OpenEndedQuestionViewSet,
    OpenEndedResponseViewSet,
    RandomQuestionViewSet,
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
router.register(r'triggers', TriggerViewSet, base_name="trigger")
router.register(r'behaviors', BehaviorViewSet)
router.register(r'actions', ActionViewSet)
router.register(r'users/actions', UserActionViewSet)
router.register(r'users/behaviors/progress', BehaviorProgressViewSet)
router.register(r'users/behaviors', UserBehaviorViewSet)
router.register(r'users/categories', UserCategoryViewSet)
router.register(r'users/goals', UserGoalViewSet)
router.register(r'users/triggers', CustomTriggerViewSet, base_name="customtrigger")

# ViewSets from the notifications app.
router.register(r'notifications/devices', GCMDeviceViewSet)
router.register(r'notifications', GCMMessageViewSet)

# ViewSets from the survey app.
router.register(r'survey/binary/responses', BinaryResponseViewSet)
router.register(r'survey/binary', BinaryQuestionViewSet)
router.register(r'survey/instruments', InstrumentViewSet)
router.register(r'survey/likert/responses', LikertResponseViewSet)
router.register(r'survey/likert', LikertQuestionViewSet)
router.register(r'survey/multiplechoice/responses', MultipleChoiceResponseViewSet)
router.register(r'survey/multiplechoice', MultipleChoiceQuestionViewSet)
router.register(r'survey/open/responses', OpenEndedResponseViewSet)
router.register(r'survey/open', OpenEndedQuestionViewSet)
router.register(r'survey', RandomQuestionViewSet, base_name="surveyrandom")

# ViewSets from the userprofile app.
router.register(r'users', UserViewSet)
router.register(r'userprofiles', UserProfileViewSet)


urlpatterns = patterns('',
    url(r'^api/auth/token/$', obtain_auth_token, name="auth-token"),
    url(r'^api/', include(router.urls)),
    url(
        r'^api/auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    url(
        r'^rules/',
        include('rules.urls', namespace='rules')
    ),
    url(r'^goals/', include('goals.urls', namespace='goals')),
    url(r'^survey/', include('survey.urls', namespace='survey')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, {'next_page': '/'}, name="logout"),
    url(r'^utils/', include('utils.urls', namespace='utils')),
    url(r'^$', IndexView.as_view())
)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
