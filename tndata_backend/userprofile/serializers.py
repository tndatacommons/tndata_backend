import hashlib

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from . import models

from goals.serializer_fields import (
    UserActionListField,
    UserBehaviorListField,
    UserCategoryListField,
    UserGoalListField,
)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.Field(source='get_full_name')
    userprofile_id = serializers.Field(source='userprofile.id')
    username = serializers.CharField(required=False)
    goals = UserGoalListField(many=True, source="usergoal_set")
    behaviors = UserBehaviorListField(many=True, source="userbehavior_set")
    actions = UserActionListField(many=True, source="useraction_set")
    categories = UserCategoryListField(many=True, source="usercategory_set")
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "full_name", 'date_joined', 'userprofile_id', "password",
            "goals", "behaviors", "actions", "categories",
        )
        read_only_fields = ("id", "date_joined", )

    def _set_user_password(self, instance, password=None):
        """Ensure that the User password gets set correctly."""
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def _generate_username(self, data):
        """NOTE: We allow users to sign up with an email/password pair. This
        method will generate a (hopefully unique) username hash using the
        email address (the first 30 chars from an md5 hex digest).
        """
        if not data.get('username', False) and 'email' in data:
            m = hashlib.md5()
            m.update(data['email'].encode("utf8"))
            data['username'] = m.hexdigest()[:30]
        return data

    def update(self, instance, validated_data):
        validated_data = self._generate_username(validated_data)
        instance = super(UserSerializer, self).update(instance, validated_data)
        instance = self._set_user_password(instance, validated_data.get('password', None))
        return instance

    def create(self, validated_data):
        validated_data = self._generate_username(validated_data)
        user = super(UserSerializer, self).create(validated_data)
        user = self._set_user_password(user, validated_data.get('password', None))
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserProfile
        fields = (
            'id', 'user', 'birthdate', 'race', 'gender', 'relationship_status',
            'educational_level', 'employment_status', 'children',
            'economic_aspiration',
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
