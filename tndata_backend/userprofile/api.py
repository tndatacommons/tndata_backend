from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import detail_route
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import models
from . import permissions
from . import serializers

# TODOs:
#
# 2. Exclude the POST forms for UserViewSet and UserProfileViewSet
#    from the browseable api.


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, )
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
        # Include the newly-created User's auth token.
        resp.data['token'] = self.object.auth_token.key
        return resp


class UserProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, )
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
