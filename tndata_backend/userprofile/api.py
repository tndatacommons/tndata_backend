from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from . import models

# TODO: Need an endpoint that allows signup and generates/returns a token.


class IsSelf(permissions.BasePermission):
    """This permission checks for a User/UserProfile's owner."""

    def has_object_permission(self, request, view, obj):
        try:
            return obj.user == request.user
        except AttributeError:
            return obj == request.user


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'is_staff')


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSelf]  # NOTE: default perms require authentication

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.UserProfile
        fields = (
            'id', 'user', 'birthdate', 'race', 'gender', 'marital_status',
        )


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = models.UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsSelf]  # NOTE: default perms require authentication

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


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
