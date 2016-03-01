from django.contrib.auth import get_user_model
from django.core import validators
from django.db.models import Q
from rest_framework import serializers

from goals import user_feed
from goals.models import (
    UserAction,
    UserBehavior,
    UserCategory,
    UserGoal,
)
from goals.serializers.v2 import (
    CustomActionSerializer,
    CustomGoalSerializer,
    GoalSerializer,
    UserActionSerializer,
    UserGoalSerializer,
    UserBehaviorSerializer,
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
from utils.decorators import cached_method
from utils.serializers import ObjectTypeModelSerializer


class UserDataSerializer(ObjectTypeModelSerializer):
    needs_onboarding = serializers.ReadOnlyField(
        source='userprofile.needs_onboarding'
    )
    places = serializers.SerializerMethodField(read_only=True)

    user_categories = serializers.SerializerMethodField(read_only=True)
    user_goals = serializers.SerializerMethodField(read_only=True)
    user_behaviors = serializers.SerializerMethodField(read_only=True)
    user_actions = serializers.SerializerMethodField(read_only=True)
    customgoals = serializers.SerializerMethodField(read_only=True)
    customactions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'needs_onboarding', 'places', 'user_categories', 'user_goals',
            'user_behaviors', 'user_actions', 'customgoals', 'customactions',
            'object_type',
        )

    def get_places(self, obj):
        qs = models.UserPlace.objects.select_related("place").filter(user=obj)
        serialized = UserPlaceSerializer(qs, many=True)
        return serialized.data

    def get_user_categories(self, obj):
        qs = UserCategory.objects.accepted_or_public(obj)
        qs = qs.select_related('category')
        serialized = UserCategorySerializer(qs, many=True)
        return serialized.data

    def get_user_goals(self, obj):
        qs = UserGoal.objects.accepted_or_public(obj).select_related('goal')
        serialized = UserGoalSerializer(qs, many=True)
        return serialized.data

    def get_user_behaviors(self, obj):
        qs = UserBehavior.objects.accepted_or_public(obj)
        qs = qs.select_related('behavior')
        serialized = UserBehaviorSerializer(qs, many=True)
        return serialized.data

    def get_user_actions(self, obj):
        qs = UserAction.objects.accepted_or_public(obj)
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

    action_feedback = serializers.SerializerMethodField(read_only=True)
    progress = serializers.SerializerMethodField(read_only=True)
    upcoming_actions = serializers.SerializerMethodField(read_only=True)
    upcoming_customactions = serializers.SerializerMethodField(read_only=True)
    suggestions = serializers.SerializerMethodField(read_only=True)
    ordering = serializers.SerializerMethodField(read_only=True)

    # This object_type helps us differentiate from different but similar enpoints
    object_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'token', 'object_type',
            'action_feedback', 'progress', 'upcoming_actions',
            'upcoming_customactions', 'ordering', 'suggestions', 'object_type',
        )
        read_only_fields = ("id", "username", "email")

    def get_object_type(self, obj):
        return "feed"

    def _get_feed(self, obj):
        """Assemble all user feed data at once because it's more efficient."""
        if not hasattr(self, "_feed"):
            self._feed = {
                'action_feedback': None,
                'progress': None,
                'upcoming_actions': [],
                'upcoming_customactions': [],
                'ordering': [],
                'suggestions': [],
                'object_type': 'feed',
            }

            if not obj.is_authenticated():
                return self._feed

            # Find the up next action and it's feedback.
            ua = user_feed.next_user_action(obj)
            if ua:
                feedback = user_feed.action_feedback(obj, ua)
                self._feed['action_feedback'] = feedback

            # Progress for today
            self._feed['progress'] = user_feed.todays_progress(obj)

            # Actions / CustomActions to do today.
            upcoming = user_feed.todays_actions(obj)
            upcoming_cas = user_feed.todays_customactions(obj)

            # Figure out the ordering.
            # This is a little confusing, but since the app cannot handle
            # heterogeneous lists, we'll construct a list that tells us the
            # ordering of the results, like: [0, 1, 0, 0], where  0's mean
            # pluck from actions, 1 customactions

            fields = ["next_trigger_date", "action__id"]
            ordering = [t + (0, ) for t in upcoming.values_list(*fields)]

            fields = ["next_trigger_date", "id"]
            ordering += [t + (1, ) for t in upcoming_cas.values_list(*fields)]
            self._feed['ordering'] = [t[2] for t in sorted(ordering)]

            # Flatten the upcoming Actions/CustomActions into IDs
            upcoming = upcoming.values_list("action__id", flat=True)
            upcoming_cas = upcoming_cas.values_list("id", flat=True)
            self._feed['upcoming_actions'] = list(upcoming)
            self._feed['upcoming_customactions'] = list(upcoming_cas)

            # Goal Suggestions
            suggestions = user_feed.suggested_goals(obj)
            srz = GoalSerializer(suggestions, many=True, user=obj)
            self._feed['suggestions'] = srz.data
        return self._feed

    def get_ordering(self, obj):
        return self._get_feed(obj)['ordering']

    def get_action_feedback(self, obj):
        return self._get_feed(obj)['action_feedback']

    def get_progress(self, obj):
        return self._get_feed(obj)['progress']

    def get_upcoming_actions(self, obj):
        return self._get_feed(obj)['upcoming_actions']

    def get_upcoming_customactions(self, obj):
        return self._get_feed(obj)['upcoming_customactions']

    def get_suggestions(self, obj):
        return self._get_feed(obj)['suggestions']


class UserSerializer(ObjectTypeModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    userprofile_id = serializers.ReadOnlyField(source='userprofile.id')
    needs_onboarding = serializers.ReadOnlyField(source='userprofile.needs_onboarding')
    username = serializers.CharField(required=False)
    timezone = serializers.ReadOnlyField(source='userprofile.timezone')
    places = serializers.SerializerMethodField(read_only=True)

    user_categories = serializers.SerializerMethodField(read_only=True)
    user_goals = serializers.SerializerMethodField(read_only=True)
    user_behaviors = serializers.SerializerMethodField(read_only=True)
    user_actions = serializers.SerializerMethodField(read_only=True)
    customgoals = serializers.SerializerMethodField(read_only=True)
    customactions = serializers.SerializerMethodField(read_only=True)

    # Wrapping all the feed data into an object.
    feed_data = serializers.SerializerMethodField(read_only=True)

    password = serializers.CharField(write_only=True)
    token = serializers.ReadOnlyField(source='auth_token.key')

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "timezone", "full_name", 'date_joined', 'userprofile_id', "password",
            'token', 'needs_onboarding', "places", "user_goals", "user_behaviors",
            "user_actions", "user_categories", 'customgoals', 'customactions',
            "feed_data", 'object_type',
        )
        read_only_fields = ("id", "date_joined", )

    def get_feed_data(self, obj):
        return {
            'action_feedback': self.get_action_feedback(obj),
            'progress': self.get_progress(obj),
            'upcoming_actions': self.get_upcoming_actions(obj),
            'upcoming_customactions': self.get_upcoming_customactions(obj),
            'suggestions': self.get_suggestions(obj),
            'object_type': 'feed',
        }

    def _get_feed(self, obj):
        """Assemble all the user feed data at once because it's more efficient."""
        if not hasattr(self, "_feed"):
            self._feed = {
                'action_feedback': None,
                'progress': None,
                'upcoming_actions': [],
                'upcoming_customactions': [],
                'suggestions': [],
            }

            if not obj.is_authenticated():
                return self._feed

            # Up next UserAction is needed to generate the feedback, and the
            # feedback is irrelevant if there's no user action
            ua = user_feed.next_user_action(obj)
            if ua:
                feedback = user_feed.action_feedback(obj, ua)
                self._feed['action_feedback'] = feedback

            # Actions to do today.
            upcoming = user_feed.todays_actions(obj)

            # Progress for today
            self._feed['progress'] = user_feed.todays_progress(obj)

            # IDs of upcoming actions/custom actions
            upcoming = upcoming.values_list("action__id", flat=True)
            self._feed['upcoming_actions'] = list(upcoming)

            upcoming_cas = user_feed.todays_customactions(obj)
            upcoming_cas = upcoming_cas.values_list("id", flat=True)
            self._feed['upcoming_customactions'] = list(upcoming_cas)

            # Goal Suggestions
            suggestions = user_feed.suggested_goals(obj)
            self._feed['suggestions'] = GoalSerializer(suggestions, many=True).data
        return self._feed

    def get_action_feedback(self, obj):
        return self._get_feed(obj)['action_feedback']

    def get_progress(self, obj):
        return self._get_feed(obj)['progress']

    def get_upcoming_customactions(self, obj):
        return self._get_feed(obj)['upcoming_customactions']

    def get_upcoming_actions(self, obj):
        return self._get_feed(obj)['upcoming_actions']

    def get_suggestions(self, obj):
        return self._get_feed(obj)['suggestions']

    @cached_method(cache_key="{0}-User.get_places", timeout=60)
    def get_places(self, obj):
        qs = models.UserPlace.objects.select_related("place").filter(user=obj)
        serialized = UserPlaceSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_user_categories", timeout=60)
    def get_user_categories(self, obj):
        qs = UserCategory.objects.accepted_or_public(obj).select_related('category')
        serialized = UserCategorySerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_user_goals", timeout=60)
    def get_user_goals(self, obj):
        qs = UserGoal.objects.accepted_or_public(obj).select_related('goal')
        serialized = UserGoalSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_user_behaviors", timeout=60)
    def get_user_behaviors(self, obj):
        qs = UserBehavior.objects.accepted_or_public(obj).select_related('behavior')
        serialized = UserBehaviorSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_user_actions", timeout=60)
    def get_user_actions(self, obj):
        qs = UserAction.objects.accepted_or_public(obj)
        serialized = UserActionSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_customgoals", timeout=60)
    def get_customgoals(self, obj):
        qs = obj.customgoal_set.all()
        serialized = CustomGoalSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_customactions", timeout=60)
    def get_customactions(self, obj):
        qs = obj.customaction_set.all()
        serialized = CustomActionSerializer(qs, many=True)
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
