from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import login, logout
from django.views.generic import TemplateView
from django.views.i18n import javascript_catalog

from axes.decorators import watch_login
from rest_framework import routers

from badgify_api.api import (
    AwardViewSet,
    BadgeViewSet,
)
from goals.api import (
    ActionViewSet,
    BehaviorViewSet,
    CategoryViewSet,
    CustomActionViewSet,
    CustomGoalViewSet,
    DailyProgressViewSet,
    GoalViewSet,
    OrganizationViewSet,
    PackageEnrollmentViewSet,
    SearchViewSet,
    TriggerViewSet,
    UserActionViewSet,
    UserBehaviorViewSet,
    UserCategoryViewSet,
    UserGoalViewSet,
)
from goals import views as goal_views
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
from userprofile.api import (
    PlaceViewSet,
    SimpleProfileViewSet,
    UserViewSet,
    UserAccountViewSet,
    UserDataViewSet,
    UserFeedViewSet,
    UserPlaceViewSet,
    UserProfileViewSet,
    api_logout,
    obtain_auth_token,
)
from rewards.api import FunContentViewSet
from utils import views as utils_views


class IndexView(TemplateView):
    """TODO: you have to sublcass TemplateView to provide extra context.
    this should probably go somewhere else.
    """
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        if not self.request.user.is_authenticated():
            form = AuthenticationForm()
            form.fields['username'].label = "Username or Email"
            context['login_form'] = form
        return context


# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()

# ViewSets from the goals app.
router.register(r'awards', AwardViewSet)
router.register(r'badges', BadgeViewSet)
router.register(r'search', SearchViewSet, base_name="search")
router.register(r'categories', CategoryViewSet)
router.register(r'goals', GoalViewSet)
router.register(r'triggers', TriggerViewSet, base_name="trigger")
router.register(r'behaviors', BehaviorViewSet)
router.register(r'actions', ActionViewSet)
router.register(r'organizations', OrganizationViewSet)
router.register(r'users/actions', UserActionViewSet)
router.register(r'users/behaviors', UserBehaviorViewSet)
router.register(r'users/categories', UserCategoryViewSet)
router.register(r'users/customgoals', CustomGoalViewSet)
router.register(r'users/customactions', CustomActionViewSet)
router.register(r'users/goals', UserGoalViewSet)
router.register(r'users/packages', PackageEnrollmentViewSet)
router.register(r'users/progress', DailyProgressViewSet)

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
router.register(r'places', PlaceViewSet)
router.register(r'users/accounts', UserAccountViewSet, base_name="useraccounts")
router.register(r'users/profile', SimpleProfileViewSet, base_name="profile")
router.register(r'users/places', UserPlaceViewSet)
router.register(r'users/data', UserDataViewSet, base_name="userdata")
router.register(r'users/feed', UserFeedViewSet, base_name="userfeed")
router.register(r'users', UserViewSet)
router.register(r'userprofiles', UserProfileViewSet)

# ViewSets from the rewards app
router.register(r'rewards', FunContentViewSet)


urlpatterns = [
    url(r'^rq/', include('django_rq.urls')),
    url(
        r'^notifications/',
        include('notifications.urls', namespace='notifications')
    ),
    url(
        r'^api/reset-password/$',
        utils_views.reset_password,
        name="reset-password"
    ),
    url(r'^api/auth/logout/$', api_logout, name="auth-logout"),
    url(r'^api/auth/token/$', obtain_auth_token, name="auth-token"),
    url(
        r'^api/users/behaviors/progress/$',
        goal_views.fake_api,
        kwargs={'option': 'behaviorprogress'},
        name="goals:fake-api"
    ),
    url(
        r'^api/users/goals/progress/average/$',
        goal_views.fake_api,
        kwargs={'option': 'goalprogressaverage'},
        name="goals:fake-api"
    ),
    url(
        r'^api/users/goals/progress/$',
        goal_views.fake_api,
        kwargs={'option': 'goalprogress'},
        name="goals:fake-api"
    ),
    url(r'^api/', include(router.urls)),
    url(
        r'^api/auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    url(r'^goals/', include('goals.urls', namespace='goals')),
    url(r'^survey/', include('survey.urls', namespace='survey')),
    url(r'^profile/', include('userprofile.urls', namespace='userprofile')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', watch_login(login), name="login"),
    url(r'^logout/$', logout, {'next_page': '/'}, name="logout"),
    url(r'^utils/', include('utils.urls', namespace='utils')),
    url(r'^jsi18n/$', javascript_catalog, {'packages': ('recurrences')}),
    url(r'^search/', include('haystack.urls')),
    url(r'^metrics/', include('redis_metrics.urls')),
    url(r'^badges/', include('badgify.urls')),
    url(r'^403/$', utils_views.FourOhThree.as_view()),
    url(r'^404/$', utils_views.FourOhFour.as_view()),
    url(r'^500/$', utils_views.FiveHundred.as_view()),
    url(r'^$', IndexView.as_view())
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
