from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from . import models
from . import permissions
from . import serializers

# TODO: Exclude the POST forms for UserViewSet and UserProfileViewSet
# from the browseable api (Ensure appropriate permissions for (un)authed users)


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

    The response includes the created user's info, such as their database id and
    the id for their created User Profile *as well as* an Auth Token for subsequent
    API requests.

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


class UserProfileViewSet(viewsets.ModelViewSet):
    """This defines methods for viewing a User Profile. User Profiles are
    created automatically after a user account is created.

    This endpoint requires authorization, and requests must include an Auth Token.

    ## Retrieving a User Profile

    Send a GET request to `/api/userprofiles/` or to
    `/api/userprofiles/{profile-id}/`. A User's profile id is available as
    part of their [user data](/api/users/). This should include a single
    result set that contains the authenticated user.

    ## Updating a User Profile

    Send a PUT request to `/api/userprofiles/{profile-id}/` including the data
    that you wish to update.

    ## Options

    View the *Options* on this page for more details regarding which fields
    are required.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)


class ObtainAuthorization(ObtainAuthToken):
    """Custom Authorization view that, in addition to the user's auth token (default
    for the superclass), returns some additional user information:

    * token
    * username
    * user_id
    * first_name
    * last_name
    * full_name
    * email

    USAGE: Send a POST request to this view containing username/password
    data and receive a JSON-encoded response.

    """
    serializer_class = serializers.AuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.object['user']
            token, created = Token.objects.get_or_create(user=serializer.object['user'])
            return Response({
                'token': token.key,
                'username': user.username,
                'user_id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'email': user.email,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

obtain_auth_token = ObtainAuthorization.as_view()
