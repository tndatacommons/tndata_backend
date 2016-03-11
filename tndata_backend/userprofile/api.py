import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout

from axes.models import AccessLog
from axes.decorators import get_ip

from rest_framework import mixins, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from goals import user_feed
from goals.serializers.v2 import GoalSerializer
from utils.mixins import VersionedViewSetMixin

from . import models
from . import permissions
from .serializers import v1, v2


logger = logging.getLogger("loggly_logs")


class PlaceViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for Places. See userprofile/api_docs for more info."""
    queryset = models.Place.objects.filter(primary=True)
    serializer_class_v1 = v1.PlaceSerializer
    serializer_class_v2 = v2.PlaceSerializer
    docstring_prefix = "userprofile/api_docs"


class UserPlaceViewSet(VersionedViewSetMixin,
                       mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    """ViewSet for UserPlaces. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserPlace.objects.all()
    serializer_class_v1 = v1.UserPlaceSerializer
    serializer_class_v2 = v2.UserPlaceSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def _quant(self, request, field, default=None):
        assert field in ['longitude', 'latitude']
        if field in request.data:
            value = Decimal(request.data[field]).quantize(Decimal('0.0001'))
            return str(value)
        return default

    def create(self, request, *args, **kwargs):
        place = request.data.get('place')
        if place:
            place, _ = models.Place.objects.get_or_create(name=place.title())
            request.data['longitude'] = self._quant(request, 'longitude')
            request.data['latitude'] = self._quant(request, 'latitude')
            request.data['place'] = place.id
            request.data['user'] = request.user.id
            request.data['profile'] = request.user.userprofile.id
            return super().create(request, *args, **kwargs)
        content = {'error': "'{}' is not a valid Place".format(place)}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        up = self.get_object()
        place = request.data.get('place')
        if place:
            place, _ = models.Place.objects.get_or_create(name=place.title())
            request.data['place'] = place.id
        else:
            request.data['place'] = up.place.id

        request.data['longitude'] = self._quant(request, 'longitude', up.longitude)
        request.data['latitude'] = self._quant(request, 'latitude', up.latitude)
        request.data['user'] = request.user.id
        request.data['profile'] = request.user.userprofile.id
        return super().update(request, *args, **kwargs)


class UserViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Users. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserSerializer
    serializer_class_v2 = v2.UserSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        qs = self.queryset.select_related("userprofile", "auth_token")
        qs = qs.filter(id=self.request.user.id)
        return qs

    def create(self, request, *args, **kwargs):
        """Alter the returned response, so that it includes an API token for a
        newly created user.
        """
        # NOTE: We expect an email address to be given, here, but this api
        # used to support a username. If we receive a username, but no email
        # address, we swap them. This'll prevent and edge case where we might
        # end up with duplicate accounts.
        if request.data.get("username") and request.data.get("email") is None:
            request.data['email'] = request.data.get('username')
            request.data.pop('username')
        resp = super(UserViewSet, self).create(request, *args, **kwargs)
        # Include the newly-created User's auth token (if we have a user)
        if hasattr(self, 'object') and hasattr(self.object, 'auth_token'):
            resp.data['token'] = self.object.auth_token.key
        return resp


class UserDataViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for User Data. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserDataSerializer
    serializer_class_v2 = v2.UserDataSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        qs = self.queryset.select_related("userprofile", "auth_token")
        qs = qs.filter(id=self.request.user.id)
        return qs


class UserFeedViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for the Feed. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserFeedSerializer
    serializer_class_v2 = v2.UserFeedSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserAccountViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """The User's account info. See userprofile/api_docs for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserAccountSerializer
    serializer_class_v2 = v2.UserAccountSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserProfileViewSet(VersionedViewSetMixin,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """The User's account info. See userprofile/api_docs for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserProfile.objects.all()
    serializer_class_v1 = v1.UserProfileSerializer
    serializer_class_v2 = v2.UserProfileSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        resp = super(UserProfileViewSet, self).list(request, *args, **kwargs)
        # Hack the data to include FQDNs for the response_url item.
        for profile in resp.data['results']:
            for q in profile['bio']:
                q['response_url'] = self.request.build_absolute_uri(q['response_url'])
                q['question_url'] = self.request.build_absolute_uri(q['question_url'])
        return resp

    def retrieve(self, request, *args, **kwargs):
        resp = super(UserProfileViewSet, self).retrieve(request, *args, **kwargs)
        profile = resp.data
        for q in profile['bio']:
            q['response_url'] = self.request.build_absolute_uri(q['response_url'])
            q['question_url'] = self.request.build_absolute_uri(q['question_url'])
        return resp

    def update(self, request, *args, **kwargs):
        """Allow setting `timezone` or `needs_onboarding`.

        * timezone: A timezone string, e.g. "America/Chicago"
        * timezone: A timezone string, e.g. "America/Chicago"

        """
        if not settings.DEBUG:
            log_msg = "User %s setting timezone to %s"
            logger.info(log_msg % (request.user.id, request.data.get('timezone', None)))
        request.data['user'] = request.user.id
        return super(UserProfileViewSet, self).update(request, *args, **kwargs)


@api_view(['POST'])
def api_logout(request):
    """This view allows a user to log out via the api (note that this returns
    rest_framework Response instances), and send additional details with the
    logout request. Here's an example scenario:

        A user logs out of their device, and sends their registration_id for
        GCM along with the logout request. That request data gets bundled with
        the logout signal, to which the notifications app is subscribed, so
        that app knows to remove the user's device & queued messages.

    To implement the above scenario, the client would a POST request containing
    the following information:

        {registration_id: 'YOUR-REGISTRATION-ID'}

    Returns a 404 if the request does not contain an authenticated user. Returns
    a 200 request upon success.

    ----

    """
    if hasattr(request, "user") and request.user:
        logout(request)  # Sends the user_logged_out signal
        return Response(None, status=status.HTTP_200_OK)
    return Response(None, status=status.HTTP_404_NOT_FOUND)


# -----------------------------------------------------------------------------
# FEED Experiments
# - another view that returns a paginated list of upcoming actions for the
#   user's feed.
# -----------------------------------------------------------------------------
@api_view(http_method_names=['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
def feed_api(request):
    """This was an experiment to create a faster, easier-to-use feed. It
    is currently disabled.

    **For the paginated list of upcoming actions, see:
    [/api/feed/upcoming/](/api/feed/upcoming/)**

    """
    # essentially the paginated amount of data do show for upcoming
    # actions and suggested goals.
    LIMIT = 5

    # This is a read-only endpoint.
    data = {
        'count': 0,
        'next': None,
        'previous': None,
        'results': []
    }

#    if request.user.is_authenticated():
#        user = request.user
#
#        # Up next UserAction / Action Feedback
#        # The Action feedback is irrelevant if there's no user action
#        ua = user_feed.next_user_action(user)
#        if ua:
#            feedback = user_feed.action_feedback(user, ua)
#            feedback['object_type'] = 'actionfeedback'
#            data['results'].append(feedback)
#
#        # Progress for today
#        progress = user_feed.todays_progress(user)
#        progress['object_type'] = 'progress'
#        data['results'].append(progress)
#
#        # Actions to do today.
#        upcoming = user_feed.todays_actions(user)
#        upcoming = upcoming.values_list("action__id", flat=True)
#        upcoming = list(upcoming)[:LIMIT]
#        upcoming_useractions = {
#            'object_type': 'upcoming',
#            'user_actions': upcoming,
#        }
#        data['results'].append(upcoming_useractions)
#
#        # Custom Actions to do today.
#        upcoming_cas = user_feed.todays_customactions(user)
#        upcoming_cas = upcoming_cas.values_list("id", flat=True)
#        upcoming_cas = list(upcoming_cas)[:LIMIT]
#        upcoming_customactions = {
#            'object_type': 'upcoming_customactions',
#            'custom_actions': upcoming_cas,
#        }
#        data['results'].append(upcoming_customactions)
#
#        # Goal Suggestions
#        goals = user_feed.suggested_goals(user)
#        goals = GoalSerializer(goals, many=True, user=user).data
#        suggestions = {
#            'goals': goals,
#            'object_type': 'suggestions'
#        }
#        data['results'].append(suggestions)
#
#    # Update our count of objects.
#    data['count'] = len(data['results'])
    return Response(data, status=status.HTTP_200_OK)


@api_view(http_method_names=['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication))
def feed_upcoming_actions_api(request):
    """All upcoming `UserAction` and `CustomAction` objects for the feed.

    This endpoint provides an array of objects containing the following items:

    - `action_id`: Integer ID for the `UserAction` or `CustomAction` object
    - `action`: A String; the title of the `Action`/`CustomAction` object.
    - `goal_id`: Integer ID for the action's parent `Goal`/`CustomGoal`.
    - `goal`: A String; the parent goal's title.
    - `category_color`: A string containing the category's hex color.
    - `trigger`: A string containing the date/time of the next scheduled reminder.
    - `type`: A string; will be 'useraction' or 'customaction'
    - `object_type`: A string; will always be 'upcoming_item'

    (NOTE: This is currently NOT paginated due to the fact that we'd have to
     fetch all of the days actions/custom actions before we can decide how
     to break it into pages).

    """
    # essentially the paginated amount of data do show for upcoming
    # actions and suggested goals.
    #LIMIT = int(request.query_params.get('page_size', 3))
    #current_page = int(request.query_params.get('page', 1))  # 1-based paging.

    # This is a read-only endpoint.
    data = {
        'count': 0,
        'next': None,
        'previous': None,
        'results': []
    }

    if request.user.is_authenticated():
        user = request.user

        #stop = (current_page * LIMIT)
        #start = (stop - LIMIT)

        # User Actions
        upcoming_uas = user_feed.todays_actions(user)
        upcoming_uas = upcoming_uas.values_list('id', flat=True)
        #upcoming_uas = list(upcoming_uas)[start:stop]
        upcoming_uas = list(upcoming_uas)

        related = ('action', 'primary_goal', 'primary_category')
        useractions = user.useraction_set.select_related(*related)
        for ua in useractions.filter(id__in=upcoming_uas):
            primary_category = ua.get_primary_category()
            primary_goal = ua.get_primary_goal()
            obj = {
                'action_id': ua.id,
                'action': ua.action.title,
                'goal_id': primary_goal.id,
                'goal': primary_goal.title,
                'category_color': primary_category.color,
                'trigger': "{}".format(ua.next_reminder),
                'type': 'useraction',
                'object_type': 'upcoming_item',
            }
            data['results'].append(obj)

        # Custom Actions
        upcoming_cas = user_feed.todays_customactions(user)
        upcoming_cas = upcoming_cas.values_list('id', flat=True)
        #upcoming_cas = list(upcoming_cas)[start:stop]
        upcoming_cas = list(upcoming_cas)

        related = ('customgoal', 'custom_trigger')
        customactions = user.customaction_set.select_related(*related)
        for ca in customactions.filter(id__in=upcoming_cas):
            obj = {
                'action_id': ca.id,
                'action': ca.title,
                'goal_id': ca.customgoal.id,
                'goal': ca.customgoal.title,
                'category_color': '#176CC4',
                'trigger': "{}".format(ca.next_reminder),
                'type': 'customaction',
                'object_type': 'upcoming_item',
            }
            data['results'].append(obj)

    # sort results (which contain UserAction/CustomAction data) by trigger
    data['results'] = sorted(data['results'], key=lambda d: d['trigger'])

    # TODO: pagination...slice by page size, BUT how will I know if/what
    # page each group of objects is going to fit into? I'd have to fetch
    # every object on every request anyway. to determin next/prev pages.
    # TODO: update next/previous if we have pages?

    data['count'] = len(data['results'])
    return Response(data, status=status.HTTP_200_OK)


class ObtainAuthorization(ObtainAuthToken):
    """Custom Authorization view that, in addition to the user's auth token
    (default for the superclass), returns some additional user information:

    * token
    * username
    * user_id
    * userprofile_id
    * first_name
    * last_name
    * full_name
    * email
    * needs_onboarding

    USAGE: Send a POST request to this view containing username/password
    data and receive a JSON-encoded response.

    """
    serializer_class = v1.AuthTokenSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data['user']
                token, created = Token.objects.get_or_create(user=user)

                gender = user.userprofile.sex
                if gender:
                    gender = gender.lower()

                return Response({
                    'token': token.key,
                    'username': user.username,
                    'id': user.id,
                    'user_id': user.id,
                    'userprofile_id': user.userprofile.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'gender': gender,
                    'needs_onboarding': user.userprofile.needs_onboarding,
                    'object_type': 'user',
                })
        except ValidationError as e:
            # Failed login attempt, record with axes
            username = request.data.get(settings.AXES_USERNAME_FORM_FIELD, None)
            if username is None:
                username = request.data.get('username', None)
            AccessLog.objects.create(
                user_agent=request.META.get('HTTP_USER_AGENT', '<unknown>')[:255],
                ip_address=get_ip(request),
                username=username,
                http_accept=request.META.get('HTTP_ACCEPT', '<unknown>'),
                path_info=request.META.get('PATH_INFO', '<unknown>'),
                trusted=False
            )
            raise e
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

obtain_auth_token = ObtainAuthorization.as_view()
