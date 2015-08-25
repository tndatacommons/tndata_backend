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


class UserViewSet(viewsets.ModelViewSet):
    """This endpoint defines methods that allow you to view, create, and update
    User accounts.

    ## Creating a User

    POST to `/api/users/` with the following information:

        {
            "username": "YOUR-USERNAME",
            "password": "YOUR-PASSWORD",
            "email": "YOUR-EMAIL",
            "first_name": "First",
            "last_name": "Last"
        }

    **Note**: `username` and `email` can be used interchangibly; You must
    provide at least one (and a password). Aslo, `first_name` and `last_name`
    are optional.

    *Valid Examples*:

        {
            "username": "YOUR-USERNAME",
            "password": "YOUR-PASSWORD",
        }

    or

        {
            "email": "YOUR-EMAIL",
            "password": "YOUR-PASSWORD",
        }


    The response includes the created user's info, such as their database id
    and the id for their created User Profile *as well as* an Auth Token for
    subsequent API requests.

    ## Acquiring an Auth token

    POST to `/api/auth/token/` with either a username/password or email/password
    pair:

        {"username": "YOUR-USERNAME", "password": "YOUR-PASSWORD"}

    or:

        {"email": "YOUR-EMAIL", "password": "YOUR-PASSWORD"}


    The response will contain a `token` attribute, which you can then include
    with subsequent requests. Include the token in an `Authorization` HTTP
    header, where the token is prefixed by the string, "Token", e.g.:

        Authorization: Token <token-value-here>

    You can use curl to test authenticated reqeusts, e.g.:

        curl -X GET http://app.tndata.org/api/users/ -H 'Authorization: Token <YOUR-TOKEN>'

    ## Logging out.

    A client of the api can log out of the api by sending a POST request to
    `/api/auth/logout/`. Include additional details in that request to trigger
    side effects (e.g. POST a `{registration_id: 'YOUR-REGISTRATION-ID'}` payload
    to remove your device's GCM registration on logout.

    ## Retrieving a User's Info

    Send a GET request to `/api/users/` or to `/api/users/{id}/`.
    This should include a single result set that contains the authenticated user.

    ## Setting a Password

    Send a PUT request to `/api/users/{id}/` including at least the following:

        {'username': <their username>, 'password': <new password>}

    ## Options

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

    def create(self, request, *args, **kwargs):
        """Alter the returned response, so that it includes an API token for a
        newly created user.
        """
        resp = super(UserViewSet, self).create(request, *args, **kwargs)
        # Include the newly-created User's auth token (if we have a user)
        if hasattr(self, 'object') and hasattr(self.object, 'auth_token'):
            resp.data['token'] = self.object.auth_token.key
        return resp


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

    Returns a 404 if the request does not contain an authenticated user. Returns
    a 200 request upon success.

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
