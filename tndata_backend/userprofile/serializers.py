from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext_lazy as _
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
            'educational_level', 'mobile_phone', 'home_phone', 'home_address',
            'home_city', 'home_state', 'home_zip',
        )
        read_only_fields = ("id", "user", )


class AuthTokenSerializer(serializers.Serializer):
    """This is similar to the AuthTokenSerializer built into django rest
    framework, but this allows either username & password or email & password
    to authenticate.  See: http://goo.gl/2HtLSm.

    """
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField()

    def _authenticate(self, username, email, password):
        """Authenticates with either username+password or email+password. Returns
        the user or None."""
        if username and password:
            return authenticate(username=username, password=password)
        if email and password:
            return authenticate(email=email, password=password)

    def _check_user(self, user):
        """Raises ValidationError if the user account is not valid or active."""
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if (username or email) and password:
            user = self._authenticate(username, email, password)
            self._check_user(user)
            attrs['user'] = user
            return attrs
        else:
            msg = _('Must include either "username" and "password" '
                    'or "email" and "password"')
            raise serializers.ValidationError(msg)
