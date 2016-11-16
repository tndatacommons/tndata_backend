from django.contrib.auth import get_user_model
from django.core import validators
from django.db.models import Q
from rest_framework import serializers

from goals import user_feed
from goals.models import (
    UserAction,
    UserCategory,
    UserGoal,
)
from goals.serializers.v2 import (
    CustomActionSerializer,
    CustomGoalSerializer,
    UserActionSerializer,
    UserGoalSerializer,
    UserCategorySerializer,
)
from .. import models

# Serializers that haven't changed from v1, imported here, but not used.
from .v1 import (  # NOQA
    PlaceSerializer,
    UserAccountSerializer,
    UserPlaceSerializer,
    UserProfileSerializer,
    AuthTokenSerializer,
)
from utils import user_utils
from utils.mixins import TombstoneMixin
from utils.serializers import ObjectTypeModelSerializer
from utils.serializer_fields import NullableDateField


class SimpleProfileSerializer(ObjectTypeModelSerializer):
    object_type = serializers.SerializerMethodField(read_only=True)
    birthday = NullableDateField()

    class Meta:
        model = models.UserProfile
        fields = (
            'id', 'user',  "timezone", 'maximum_daily_notifications',
            'needs_onboarding', 'zipcode', 'birthday', 'sex', 'employed',
            'is_parent', 'in_relationship', 'has_degree', 'updated_on',
            'created_on', 'object_type',
        )
        read_only_fields = (
            "id", "user", "updated_on", "created_on", "object_type",
        )

    def get_object_type(self, obj):
        return 'profile'


class UserDataSerializer(TombstoneMixin, ObjectTypeModelSerializer):
    # TODO: Kill this and the related endpoint
    needs_onboarding = serializers.ReadOnlyField(
        source='userprofile.needs_onboarding'
    )
    places = serializers.SerializerMethodField(read_only=True)

    user_categories = serializers.SerializerMethodField(read_only=True)
    user_goals = serializers.SerializerMethodField(read_only=True)
    user_actions = serializers.SerializerMethodField(read_only=True)
    customgoals = serializers.SerializerMethodField(read_only=True)
    customactions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'needs_onboarding', 'places', 'user_categories', 'user_goals',
            'user_actions', 'customgoals', 'customactions',
            'object_type',
        )

    def get_places(self, obj):
        qs = models.UserPlace.objects.select_related("place").filter(user=obj)
        serialized = UserPlaceSerializer(qs, many=True)
        return serialized.data

    def get_user_categories(self, obj):
        qs = UserCategory.objects.published(user=obj)
        qs = qs.select_related('category')
        serialized = UserCategorySerializer(qs, many=True)
        return serialized.data

    def get_user_goals(self, obj):
        qs = UserGoal.objects.published(user=obj).select_related('goal')
        serialized = UserGoalSerializer(qs, many=True)
        return serialized.data

    def get_user_actions(self, obj):
        qs = UserAction.objects.published(user=obj)
        serialized = UserActionSerializer(qs, many=True)
        return serialized.data

    def get_customgoals(self, obj):
        qs = obj.customgoal_set.all()
        serialized = CustomGoalSerializer(qs, many=True)
        return serialized.data

    def get_customactions(self, obj):
        qs = obj.customaction_set.all()
        serialized = CustomActionSerializer(qs, many=True)
        return serialized.data


class UserFeedSerializer(ObjectTypeModelSerializer):
    token = serializers.ReadOnlyField(source='auth_token.key')

    progress = serializers.SerializerMethodField(read_only=True)
    suggestions = serializers.SerializerMethodField(read_only=True)
    upcoming = serializers.SerializerMethodField(read_only=True)
    streaks = serializers.SerializerMethodField(read_only=True)
    funcontent = serializers.SerializerMethodField(read_only=True)

    # This object_type helps us differentiate from different but similar enpoints
    object_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'token', 'object_type', 'upcoming',
            'streaks', 'progress', 'suggestions', 'funcontent',
            'object_type',
        )
        read_only_fields = ("id", "username", "email")

    def get_object_type(self, obj):
        return "feed"

    def _get_feed(self, obj):
        """Assemble all user feed data at once because it's more efficient."""
        # note: obj == a user
        if not obj.is_authenticated():
            return {}

        if not hasattr(self, '_feed_results'):
            self._feed_results = user_feed.feed_data(obj)
        return self._feed_results

    def get_progress(self, obj):
        return self._get_feed(obj)['progress']

    def get_upcoming(self, obj):
        return self._get_feed(obj)['upcoming']

    def get_streaks(self, obj):
        return self._get_feed(obj)['streaks']

    def get_funcontent(self, obj):
        return self._get_feed(obj)['funcontent']

    def get_suggestions(self, obj):
        return []


class UserSerializer(ObjectTypeModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    userprofile_id = serializers.ReadOnlyField(source='userprofile.id')
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    token = serializers.ReadOnlyField(source='auth_token.key')
    needs_onboarding = serializers.ReadOnlyField(
        source='userprofile.needs_onboarding'
    )

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "full_name", 'date_joined', 'userprofile_id', "password",
            'token', 'needs_onboarding', 'object_type',
        )
        read_only_fields = ("id", "date_joined", )

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
