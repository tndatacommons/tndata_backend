import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout

from rest_framework import mixins, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import models
from . import permissions
from . import serializers

logger = logging.getLogger("loggly_logs")


class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    """Places are named locations. They may be pre-defined or user-defined.
    Each place contains the following fields:

    * id: The unique database id of the place.
    * name: The unique name of the place.
    * slug: A slugified version of the name (unique)
    * primary: Primary places should be used to generate menus. This endpoint
      currently _only_ displays primary places (so this is always True).
    * updated_on: Date the place was updated.
    * created_on: Date the place was created.

    This is a read-only endpoint. To save a place, see
    the [UserPlaces API](/api/users/places/).

    ----

    """
    queryset = models.Place.objects.filter(primary=True)
    serializer_class = serializers.PlaceSerializer


class UserPlaceViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    """User Places are Places defined by a user. A `UserPlace` object consists
    of the following fields:

    * id: The unique database id of the place.
    * user: The user's unique database ID.
    * profile: The user's unique profile ID (see the
      [/api/userprofiles/](/api/userprofiles/) endpoint)
    * place: A hash represnting the name of a place. See the
      [/api/users/places/](/api/users/places/) endpoint.
    * latitude: A decimal value representing the latitude of the place.
    * longitude: A decimal value representing the longitude of the place.
    * updated_on: Date the place was updated.
    * created_on: Date the place was created.

    ## Creating a UserPlace

    POST to `/api/users/places/` with the following information:

        {
            "place": "PLACE-NAME"        // e.g. 'Home' or 'Work'
            "latitude": "LATITUDE",      // e.g. '35.1234'
            "longitude": "LONGITUDE",    // e.g. '-89.1234'
        }

    ## Updating a UserPlace

    A UserPlace instance has a unique resource URI based on it's Database ID,
    e.g. `/api/users/places/1/`. To update this object, send a PUT request
    containing values that you want to update, e.g.:

        {
            "latitude": "27.9881",
            "longitude": "86.9253"
        }

    **NOTE**: A user can define only _one Place name_. For example, if a user
    sets a `Home` location, they can have only one UserPlace objects where
    `place` is set to "Home".

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserPlace.objects.all()
    serializer_class = serializers.UserPlaceSerializer
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


class UserViewSet(viewsets.ModelViewSet):
    """This endpoint defines methods that allow you to view, create, and update
    User accounts. Additionally, it exposes several bits of user data, therefore
    acting as a decently complete single point of information for a User.

    Sections in this documentation:

    * <a href="#user-data">User Data</a>
    * <a href="#creating-a-user">Creating a User</a>
    * <a href="#acquiring-an-auth-token">Acquiring an Auth token</a>
    * <a href="#logging-out">Logging Out</a>
    * <a href="#retrieving-a-users-info">Retrieveing a User's Info</a>
    * <a href="#setting-a-password">Setting a Password</a>
    * <a href="#options">Options</a>

    ----

    ## User Data

    The following user data is available from this endpoint as an item in the
    `results` array.

    * `id` -- Unique database ID for the User.
    * `username` -- The user's username. For users that sign up through the app,
      the is a unique hash and is not human-friendly.
    * `email` -- the user's email address.
    * `is_staff` -- True or False: Indicates if users can log in to admin tools.
    * `first_name` -- The user's first name.
    * `last_name` -- The user's last name.
    * `full_name` -- Combination of first and last name
    * `timezone` -- The user's given timezone.
    * `date_joined` -- Date the user joined.
    * `userprofile_id` -- Unique ID for the [UserProfile](/api/userprofiles/)
    * `token` -- The user's [auth token](#acquiring-an-autho-token)
    * `needs_onboarding` -- Whether or not the user should go through onboarding.

    Collections of related data for the user, include:

    * `next_action` -- a `UserAction` object (the mapping between a User and
      an Action`. This is the upcoming activity for the user.
    * `action_feedback` is a object of data for the _feedback card_ related to
      the user's `next_action`. It's intention is to _reinforce the user's
      upcoming action with some motivational text_. This content is dynamically
      generated, and will depend on the percentage of completed vs scheduled
      actions for the user. It contains the following data:

        - `title`: Title-text for the motivational message.
        - `subtitle`: A short additional motivational message.
        - `percentage`: percentage of actions completed in some time period.
        - `incomplete`: Number of actions the user did not complete in some
          time period.
        - `completed`: Number of actions completed in some time period.
        - `total`: Number of actions schedule in some time period.
        - `icon`: An integer (1-4) indicating which icon should be used.
          (1: footsteps, 2: thumbs-up, 3: ribbon, 4: trophy (when all are completed))

    * `progress` -- an object containing the number of actions completed today,
      the number of total actions scheduled for today, and the percentage of
      those completed.
    * `upcoming_actions` -- a list of the `UserAction`s that are relevant for
      today (i.e. the user has a reminder scheduled for today)
    * `suggestions` -- a list of suggested `Goal`s for the user.

    * `places` -- An array of the [user's Places](/api/users/places/)
    * `goals` -- An array of the user's selected [Goals](/api/users/goals/). Each
      of these objects also contains data representing the user's `GoalProgress`
      data. See the [UserGoal documentation](/api/users/goals/) for more info.
    * `behaviors` -- An array of the user's selected [Behaviors](/api/users/behaviors/).
      Each of these objects also contains data representing the user's
      `BehaviorProgress`. See the [UserBehavior documentation](/api/users/behaviors/)
      for more info.
    * `actions` -- An array of the user's selected [Actions](/api/users/actions/)
    * `categories` -- An array of the user's [Categories](/api/users/categories/)

    ## Creating a User <a href="#creating-a-user">&para;</a>

    POST to `/api/users/` with the following information:

        {
            "email": "YOUR-EMAIL",
            "password": "YOUR-PASSWORD",
            "first_name": "First",
            "last_name": "Last"
        }

    **Note**: `email` and `password` are required! However, `first_name` and
    `last_name` are optional.

    *Valid Example*:

        {
            "email": "YOUR-EMAIL",
            "password": "YOUR-PASSWORD",
        }


    The response includes the created user's info, such as their database id
    and the id for their created User Profile *as well as* an Auth Token for
    subsequent API requests.

    ## Acquiring an Auth token <a href="#acquiring-an-auth-token">&para;</a>

    POST to `/api/auth/token/` with either an  email/password pair:

        {"email": "YOUR-EMAIL", "password": "YOUR-PASSWORD"}


    The response will contain a `token` attribute, which you can then include
    with subsequent requests. Include the token in an `Authorization` HTTP
    header, where the token is prefixed by the string, "Token", e.g.:

        Authorization: Token <token-value-here>

    You can use curl to test authenticated reqeusts, e.g.:

        curl -X GET http://app.tndata.org/api/users/ -H 'Authorization: Token <YOUR-TOKEN>'

    ## Logging out <a href="#logging-out">&para;</a>

    A client of the api can log out of the api by sending a POST request to
    `/api/auth/logout/`. Include additional details in that request to trigger
    side effects (e.g. POST a `{registration_id: 'YOUR-REGISTRATION-ID'}` payload
    to remove your device's GCM registration on logout.

    ## Retrieving a User's Info <a href="#retrieving-a-users-info">&para;</a>

    Send a GET request to `/api/users/` or to `/api/users/{id}/`.
    This should include a single result set that contains the authenticated user.

    ## Setting a Password <a href="#setting-a-password">&para;</a>

    Send a PUT request to `/api/users/{id}/` including at least the following:

        {'username': <their username>, 'password': <new password>}

    ## Options <a href="#options">&para;</a>

    See the *Options* on this page for more information regarding which fields
    are required (during PUT requests).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)

#    def _serialized_data_for_list(self, user, page_or_queryset, timeout=None):
#        """NOTE: This method is not currently cached due to the difficulty
#        of defining an appropriate cache invalidation scheme.
#
#        This method is a hook to cache the entire set of data for this
#        (otherwise slow and unwieldy) viewset.
#
#        Arguments for this method:
#
#        * user -- the user's ID is used as part of the cache key
#        * page_or_queryset -- the paginated or plain old queryset of data
#        * timeout -- default is None (meaning never expire)
#
#        NOTE on timeout: we want to keep this page cached as long as possible,
#        so it's up to you to invalidate the cache for this viewset. The
#        cache key is of the form: `userviewset-{userid}`.
#
#        See the `reset_userviewset_cache` signal handler in this file.
#
#        """
#        if not user.is_authenticated():
#            return self.get_serializer(page_or_queryset, many=True)
#
#        key = 'userviewset-{}'.format(user.id)
#        data = cache.get(key)
#        if data is not None:
#            log_msg = "Returning cached /api/users/ data for {}".format(user.email)
#            post_message("#tech", log_msg)
#            return data
#        else:
#            log_msg = "NOT Cached: /api/users/ data for {}, setting cache"
#            post_message("#tech", log_msg.format(user.email))
#
#        serializer = self.get_serializer(page_or_queryset, many=True)
#        #cache.set(key, serializer.data, timeout=timeout)
#        return serializer.data
#
#    def list(self, request, *args, **kwargs):
#        """Override the list method from the ListModelMixin, so we can cache
#        the Serializer's results.
#
#        """
#        queryset = self.filter_queryset(self.get_queryset())
#        page = self.paginate_queryset(queryset)
#        if page is not None:
#            data = self._serialized_data_for_list(request.user, page)
#            return self.get_paginated_response(data)
#
#        data = self._serialized_data_for_list(request.user, queryset)
#        return Response(data)

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


class UserDataViewSet(viewsets.ModelViewSet):
    """
    An attempt an a more efficient api to expose user data.

    ## Data Fields

    Most of the data fields on this endpoint are fairly straightforward, and
    share a lot of similarities with `/api/users/`. The differences include:

    - `places` -- all of a user's defined [Places](/api/users/places/).
    - `categories`, `goals`, `behaviors`, `actions` have fewer nested attributes.
      This makes the queries to populate this data much less complex (and faster)
    - a `data_graph` attribute exists here that explains the nested relationship
      for the user's selected content (see below)

    ## Data Graph

    This attribute contains a list of `[parent_id, object_id]` arrays that
    show the relationship graph for a user's selected content. Note that these
    are IDs for the Category, Goal, Behavior, and Action models, and are NOT
    the User* models (i.e. not the mapping ids).

    The `primary_categories` attribute is a list of each goal's primary category
    (or null if there are none), while the `primary_goals` attribute is a list
    of each Action's primary goal (or null).

        {
            'categories': [
                [<category_id>, <goal_id>], ...
            ],
            'goals': [
                [<goal_id>, <behavior_id>], ...
            ],
            'behaviors': [
                [<behavior_id>, <action_id>], ...
            ],
            'primary_categories': [
                [<goal_id>, <category_id>], ...
            ],
            'primary_goals': [
                [<action_id>, <goal_id>], ...
            ],
        }

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserDataSerializer
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserFeedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The User Feed of information: home-feed data for the user, include:

    * `next_action` -- a `UserAction` object (the mapping between a User and
      an Action`. This is the upcoming activity for the user.
    * `action_feedback` is a object of data for the _feedback card_ related to
      the user's `next_action`. It's intention is to _reinforce the user's
      upcoming action with some motivational text_. This content is dynamically
      generated, and will depend on the percentage of completed vs scheduled
      actions for the user. It contains the following data:

        - `title`: Title-text for the motivational message.
        - `subtitle`: A short additional motivational message.
        - `percentage`: percentage of actions completed in some time period.
        - `incomplete`: Number of actions the user did not complete in some
          time period.
        - `completed`: Number of actions completed in some time period.
        - `total`: Number of actions schedule in some time period.
        - `icon`: An integer (1-4) indicating which icon should be used.
          (1: footsteps, 2: thumbs-up, 3: ribbon, 4: trophy (when all are completed))

    * `progress` -- an object containing the number of actions completed today,
      the number of total actions scheduled for today, and the percentage of
      those completed.
    * `upcoming_actions` -- a list of the `UserAction`s that are relevant for
      today (i.e. the user has a reminder scheduled for today)
    * `suggestions` -- a list of suggested `Goal`s for the user.
    * `user_categories` -- The user's selected categories.
    * `user_goals` -- The user's selected goals.


    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserFeedSerializer
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserAccountViewSet(viewsets.ModelViewSet):
    """The User's account info.

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserAccountSerializer
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserProfileViewSet(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """This defines methods for viewing and updating a User's _Profile_. User
    Profiles are created automatically after a user account is created.

    ## Updating

    Currently the only portion of a UserProfile that can be updated is their
    `timezone` and the `needs_onboarding` fields. To set a user's timezone,
    send a PUT request to the UserProfile's detail endpoint,
    `/api/userprofiles/{userprofile_id}/`, including the string for the
    desired timezone.

        {'timezone': 'America/Chicago'}

    Or to update both fields:

        {'timezone': 'America/Chicago', 'needs_onboarding': false}

    ## Retrieving a User Profile

    Send a GET request to `/api/userprofiles/` or to
    `/api/userprofiles/{profile-id}/`. A User's profile id is available as
    part of their [user data](/api/users/). This should include a single
    result set that contains the authenticated user.

    ## Bio Information

    The `bio` attribute contains the questions and the authenticated user's
    answers (if any) to the
    [Bio survey](http://app.tndata.org/api/survey/instruments/4/).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer
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
    serializer_class = serializers.AuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
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
                'needs_onboarding': user.userprofile.needs_onboarding,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

obtain_auth_token = ObtainAuthorization.as_view()
