from django.contrib.auth import authenticate, get_user_model
from django.core import validators
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from goals import user_feed
from goals.models import (
    UserAction,
    UserBehavior,
    UserCategory,
    UserGoal,
)
from goals.serializers.v1 import (
    GoalSerializer,
    ReadOnlyUserActionSerializer,
    ReadOnlyUserGoalSerializer,
    UserBehaviorSerializer,
    UserCategorySerializer,
)
from goals.serializers.simple import (
    SimpleGoalSerializer,
    SimpleUserBehaviorSerializer,
    SimpleUserCategorySerializer,
)
from utils import user_utils
from utils.decorators import cached_method
from utils.serializers import ObjectTypeModelSerializer

from .. import models


class PlaceSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = models.Place
        fields = (
            'id', 'name', 'slug', 'primary', 'updated_on', 'created_on',
            'object_type',
        )


class PlaceField(serializers.RelatedField):

    def to_internal_value(self, data):
        return models.Place.objects.get(pk=data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'name': value.name,
            'slug': value.slug,
            'primary': value.primary,
        }


class UserPlaceSerializer(ObjectTypeModelSerializer):
    place = PlaceField(queryset=models.Place.objects.all())

    class Meta:
        model = models.UserPlace
        fields = (
            'id', 'user', 'profile', 'place', 'latitude', 'longitude',
            'object_type',
        )
        read_only_fields = ("id", "updated_on", "created_on", )


class UserAccountSerializer(ObjectTypeModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    userprofile_id = serializers.ReadOnlyField(source='userprofile.id')
    needs_onboarding = serializers.ReadOnlyField(source='userprofile.needs_onboarding')
    username = serializers.CharField(required=False)
    timezone = serializers.ReadOnlyField(source='userprofile.timezone')
    password = serializers.CharField(write_only=True)
    token = serializers.ReadOnlyField(source='auth_token.key')

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "timezone", "full_name", 'date_joined', 'userprofile_id', "password",
            'token', 'needs_onboarding',
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
        instance = super().update(instance, validated_data)
        instance = self._set_user_password(instance, validated_data.get('password', None))
        return instance

    def create(self, validated_data):
        validated_data = self._generate_username(validated_data)
        user = super().create(validated_data)
        user = self._set_user_password(user, validated_data.get('password', None))
        return user


class UserSerializer(ObjectTypeModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    userprofile_id = serializers.ReadOnlyField(source='userprofile.id')
    needs_onboarding = serializers.ReadOnlyField(source='userprofile.needs_onboarding')
    username = serializers.CharField(required=False)
    timezone = serializers.ReadOnlyField(source='userprofile.timezone')
    places = serializers.SerializerMethodField(read_only=True)

    categories = serializers.SerializerMethodField(read_only=True)
    goals = serializers.SerializerMethodField(read_only=True)
    behaviors = serializers.SerializerMethodField(read_only=True)
    actions = serializers.SerializerMethodField(read_only=True)

    next_action = serializers.SerializerMethodField(read_only=True)
    action_feedback = serializers.SerializerMethodField(read_only=True)
    progress = serializers.SerializerMethodField(read_only=True)
    upcoming_actions = serializers.SerializerMethodField(read_only=True)
    suggestions = serializers.SerializerMethodField(read_only=True)

    password = serializers.CharField(write_only=True)
    token = serializers.ReadOnlyField(source='auth_token.key')

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "timezone", "full_name", 'date_joined', 'userprofile_id', "password",
            'token', 'needs_onboarding', "places", "goals", "behaviors",
            "actions", "categories", "next_action", "action_feedback",
            "progress", "upcoming_actions", "suggestions",
        )
        read_only_fields = ("id", "date_joined", )

    def _get_feed(self, obj):
        """Assemble all the user feed data at once because it's more efficient."""
        if not hasattr(self, "_feed"):
            self._feed = {
                'next_action': None,
                'action_feedback': None,
                'progress': None,
                'upcoming_actions': [],
                'suggestions': [],
            }

            if not obj.is_authenticated():
                return self._feed

            # Up next UserAction
            ua = user_feed.next_user_action(obj)
            self._feed['next_action'] = ReadOnlyUserActionSerializer(ua).data
            if ua:
                # The Action feedback is irrelevant if there's no user action
                feedback = user_feed.action_feedback(obj, ua)
                self._feed['action_feedback'] = feedback

            # Actions to do today.
            upcoming = user_feed.todays_actions(obj)

            # Progress for today
            self._feed['progress'] = user_feed.todays_actions_progress(obj)
            upcoming = ReadOnlyUserActionSerializer(upcoming, many=True).data
            self._feed['upcoming_actions'] = upcoming

            # Goal Suggestions
            suggestions = user_feed.suggested_goals(obj)
            self._feed['suggestions'] = GoalSerializer(suggestions, many=True).data
        return self._feed

    def get_next_action(self, obj):
        return self._get_feed(obj)['next_action']

    def get_action_feedback(self, obj):
        return self._get_feed(obj)['action_feedback']

    def get_progress(self, obj):
        return self._get_feed(obj)['progress']

    def get_upcoming_actions(self, obj):
        return self._get_feed(obj)['upcoming_actions']

    def get_suggestions(self, obj):
        return self._get_feed(obj)['suggestions']

    @cached_method(cache_key="{0}-User.get_places", timeout=60)
    def get_places(self, obj):
        qs = models.UserPlace.objects.select_related("place").filter(user=obj)
        serialized = UserPlaceSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_categories", timeout=60)
    def get_categories(self, obj):
        qs = UserCategory.objects.accepted_or_public(obj).select_related('category')
        serialized = UserCategorySerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_goals", timeout=60)
    def get_goals(self, obj):
        qs = UserGoal.objects.accepted_or_public(obj).select_related('goal')
        serialized = ReadOnlyUserGoalSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_behaviors", timeout=60)
    def get_behaviors(self, obj):
        qs = UserBehavior.objects.accepted_or_public(obj).select_related('behavior')
        serialized = UserBehaviorSerializer(qs, many=True)
        return serialized.data

    @cached_method(cache_key="{0}-User.get_actions", timeout=60)
    def get_actions(self, obj):
        qs = UserAction.objects.accepted_or_public(obj)
        serialized = ReadOnlyUserActionSerializer(qs, many=True)
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


class UserDataSerializer(ObjectTypeModelSerializer):
    token = serializers.ReadOnlyField(source='auth_token.key')
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
    data_graph = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'is_staff', 'first_name', 'last_name',
            "timezone", "full_name", 'date_joined', 'userprofile_id',
            'token', 'needs_onboarding', 'places',
            'user_categories', 'user_goals', 'user_behaviors', 'user_actions',
            'data_graph',
        )
        read_only_fields = ("id", "date_joined", )

    def get_places(self, obj):
        qs = models.UserPlace.objects.select_related("place").filter(user=obj)
        serialized = UserPlaceSerializer(qs, many=True)
        return serialized.data

    def get_user_categories(self, obj):
        qs = UserCategory.objects.accepted_or_public(obj).select_related('category')
        serialized = SimpleUserCategorySerializer(qs, many=True)
        return serialized.data

    def get_user_goals(self, obj):
        qs = UserGoal.objects.accepted_or_public(obj).select_related('goal')
        serialized = ReadOnlyUserGoalSerializer(qs, many=True)
        return serialized.data

    def get_user_behaviors(self, obj):
        qs = UserBehavior.objects.accepted_or_public(obj).select_related('behavior')
        serialized = SimpleUserBehaviorSerializer(qs, many=True)
        return serialized.data

    def get_user_actions(self, obj):
        qs = UserAction.objects.accepted_or_public(obj)
        serialized = ReadOnlyUserActionSerializer(qs, many=True)
        return serialized.data

    def get_data_graph(self, obj):
        """This is a list of the user's selected content, organized so we can
        see the relationships from one model to another. The result is a
        dictionary containing lists of IDs:

            {
                'categories': [
                    [<category_id>, <goal_id>], ...
                ],
                'goals': [
                    [<goal_id>, <behavior_id>], ...
                ],
                'behaviors': [
                    [<behavior_id>, <action_id>], ...
                ],
                'primary_categories': [
                    [<goal_id>, <category_id>], ...
                ],
                'primary_goals': [
                    [<action_id>, <goal_id>], ...
                ],
            }

        NOTE: These are IDs for the Category, Goal, Behavior, and Action models,
        and are NOT the User* models.

        """
        # user's selected Goal IDs + parent Category IDs
        cg = obj.usergoal_set.values_list('goal__categories', 'goal__id')

        # user's selected Behavior IDs + parent Goal IDs
        gb = obj.userbehavior_set.values_list('behavior__goals', 'behavior__id')

        # user's selected Action IDs + parent Behavior IDs
        ba = obj.useraction_set.values_list('action__behavior__id', 'action__id')

        # For a goal's primary category, we'r just keeping the first one we find
        # primary_categories: [[<goal_id>, <primary_category_id>], ...]
        pcats = {}
        for catid, goalid in cg:
            if goalid not in pcats:
                pcats[goalid] = catid
        pcats = [[gid, catid] for gid, catid in pcats.items()]

        # The Actions' primary Goal
        # primary_goals: [[<action_id>, <primary_goal_id>], ...]
        pgoals = obj.useraction_set.values_list('action__id', 'primary_goal__id')

        return {
            'categories': list(cg),
            'goals': list(gb),
            'behaviors': list(ba),
            'primary_categories': list(pcats),
            'primary_goals': list(pgoals),
        }


class UserFeedSerializer(ObjectTypeModelSerializer):
    token = serializers.ReadOnlyField(source='auth_token.key')

    next_action = serializers.SerializerMethodField(read_only=True)
    action_feedback = serializers.SerializerMethodField(read_only=True)
    progress = serializers.SerializerMethodField(read_only=True)
    upcoming_actions = serializers.SerializerMethodField(read_only=True)
    suggestions = serializers.SerializerMethodField(read_only=True)

    user_categories = serializers.SerializerMethodField(read_only=True)
    user_goals = serializers.SerializerMethodField(read_only=True)

    # This object_type helps us differentiate from different but similar enpoints
    object_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'token', 'object_type',
            'next_action', 'action_feedback', 'progress',
            'upcoming_actions', 'suggestions',
            'user_categories', 'user_goals',
        )
        read_only_fields = ("id", "username", "email")

    def get_object_type(self, obj):
        return "feed"

    def get_user_categories(self, obj):
        qs = UserCategory.objects.accepted_or_public(obj).select_related('category')
        serialized = SimpleUserCategorySerializer(qs, many=True)
        return serialized.data

    def get_user_goals(self, obj):
        qs = UserGoal.objects.accepted_or_public(obj).select_related('goal')
        serialized = ReadOnlyUserGoalSerializer(qs, many=True)
        return serialized.data

    def _get_feed(self, obj):
        """Assemble all user feed data at once because it's more efficient."""
        if not hasattr(self, "_feed"):
            self._feed = {
                'next_action': None,
                'action_feedback': None,
                'progress': None,
                'upcoming_actions': [],
                'suggestions': [],
            }

            if not obj.is_authenticated():
                return self._feed

            # Up next UserAction
            ua = user_feed.next_user_action(obj)
            self._feed['next_action'] = ReadOnlyUserActionSerializer(ua).data
            if ua:
                # The Action feedback is irrelevant if there's no user action
                feedback = user_feed.action_feedback(obj, ua)
                self._feed['action_feedback'] = feedback

            # Actions to do today.
            upcoming = user_feed.todays_actions(obj)

            # Progress for today
            self._feed['progress'] = user_feed.todays_actions_progress(obj)
            upcoming = ReadOnlyUserActionSerializer(upcoming, many=True).data
            self._feed['upcoming_actions'] = upcoming

            # Goal Suggestions
            suggestions = user_feed.suggested_goals(obj)
            srz = SimpleGoalSerializer(suggestions, many=True, user=obj)
            self._feed['suggestions'] = srz.data
        return self._feed

    def get_next_action(self, obj):
        return self._get_feed(obj)['next_action']

    def get_action_feedback(self, obj):
        return self._get_feed(obj)['action_feedback']

    def get_progress(self, obj):
        return self._get_feed(obj)['progress']

    def get_upcoming_actions(self, obj):
        return self._get_feed(obj)['upcoming_actions']

    def get_suggestions(self, obj):
        return self._get_feed(obj)['suggestions']


class UserProfileSerializer(ObjectTypeModelSerializer):
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
