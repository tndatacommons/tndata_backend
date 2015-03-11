from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import models


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.Field(source='get_full_name')
    userprofile_id = serializers.Field(source='userprofile.id')

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "full_name", 'date_joined', 'userprofile_id', "password",
        )
        read_only_fields = ("id", "date_joined", )
        write_only_fields = ("password", )

    def _set_user_password(self, user, attrs):
        """Ensure that the User password gets set correctly."""
        password = attrs.get('password', None)
        if password:
            user.set_password(password)
        return user

    def restore_object(self, attrs, instance=None):
        user = super(UserSerializer, self).restore_object(attrs, instance)
        user = self._set_user_password(user, attrs)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserProfile
        fields = (
            'id', 'user', 'birthdate', 'race', 'gender', 'marital_status',
        )
        read_only_fields = ("id", "user", )
