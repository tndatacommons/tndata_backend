from django.contrib.auth import authenticate, get_user_model
from django.core import validators
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from goals.models import (
    UserBehavior,
    UserCategory,
    UserGoal,
)
from goals.serializers import (
    UserActionSerializer,
    UserBehaviorSerializer,
    UserCategorySerializer,
    UserGoalSerializer,
)
from . import models
from utils import user_utils


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    userprofile_id = serializers.ReadOnlyField(source='userprofile.id')
    needs_onboarding = serializers.ReadOnlyField(source='userprofile.needs_onboarding')
    username = serializers.CharField(required=False)
    timezone = serializers.ReadOnlyField(source='userprofile.timezone')

    categories = serializers.SerializerMethodField(read_only=True)
    goals = serializers.SerializerMethodField(read_only=True)
    behaviors = serializers.SerializerMethodField(read_only=True)
    actions = UserActionSerializer(
        many=True,
        source="useraction_set",
        read_only=True,
    )
    password = serializers.CharField(write_only=True)
    token = serializers.ReadOnlyField(source='auth_token.key')

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "timezone", "full_name", 'date_joined', 'userprofile_id', "password",
            "goals", "behaviors", "actions", "categories", 'token',
            'needs_onboarding',
        )
        read_only_fields = ("id", "date_joined", )

    def get_categories(self, obj):
        qs = UserCategory.objects.accepted_or_public(obj)
        serialized = UserCategorySerializer(qs, many=True)
        return serialized.data

    def get_goals(self, obj):
        qs = UserGoal.objects.accepted_or_public(obj)
        serialized = UserGoalSerializer(qs, many=True)
        return serialized.data

    def get_behaviors(self, obj):
        qs = UserBehavior.objects.accepted_or_public(obj)
        serialized = UserBehaviorSerializer(qs, many=True)
        return serialized.data

    def validate_username(self, value):
        User = get_user_model()
        if not self.partial and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This user account already exists.")
        return value

    def validate_email(self, value):
        """Validate several things, given a user's email:

        * this is a valid email address
        * there are no existing users with this email
        * there are no users with a username hashed from this email

        """
        User = get_user_model()
        criteria = (Q(email=value) | Q(username=user_utils.username_hash(value)))
        if not self.partial and User.objects.filter(criteria).exists():
            raise serializers.ValidationError("This user account already exists.")
        validators.validate_email(value)
        return value

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
            data['username'] = user_utils.username_hash(data['email'])
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
    bio = serializers.ReadOnlyField(required=False)

    class Meta:
        model = models.UserProfile
        fields = ('id', 'user', 'timezone', 'needs_onboarding', 'bio')


class AuthTokenSerializer(serializers.Serializer):
    """This is similar to the AuthTokenSerializer built into django rest
    framework, but this allows either username & password or email & password
    to authenticate.  See: http://goo.gl/2HtLSm.

    """
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(style={'input_type': 'password'})

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
