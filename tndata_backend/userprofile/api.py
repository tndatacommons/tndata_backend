from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, viewsets

from . import models


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
    permission_classes = [permissions.IsAuthenticated, IsSelf]

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
    permission_classes = [permissions.IsAuthenticated, IsSelf]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
