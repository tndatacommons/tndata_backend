from django.conf import settings
from rest_framework import serializers
from utils.mixins import TombstoneMixin
from utils.serializers import ObjectTypeModelSerializer
from utils.serializer_fields import ReadOnlyDatetimeField

from ..models import (
    Action,
    Behavior,
    Category,
    DailyProgress,
    Goal,
    Organization,
    Program,
    Trigger,
    UserAction,
    UserGoal,
    UserBehavior,
    UserCategory,
)
from ..serializer_fields import (
    CustomTriggerField,
    SimpleActionField,
    SimpleBehaviorField,
    SimpleCategoryField,
    SimpleGoalField,
    SimpleTriggerField,
)

# XXX: Things we don't want to change from v1
from .v1 import (  # flake8: noqa
    CustomActionSerializer,
    CustomGoalSerializer,
    PackageEnrollmentSerializer,
    ReadOnlyUserActionSerializer,
    TriggerSerializer,
)


class ProgramSerializer(ObjectTypeModelSerializer):
    organization = serializers.ReadOnlyField(source='organization.name')

    class Meta:
        model = Program
        fields = ('id', 'name', 'name_slug', 'organization', 'object_type')


class OrganizationSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'name_slug', 'object_type')


class DailyProgressSerializer(ObjectTypeModelSerializer):
    engagement_rank = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DailyProgress
        fields = (
            'id', 'user', 'actions_total', 'actions_completed', 'actions_snoozed',
            'actions_dismissed', 'customactions_total', 'customactions_completed',
            'customactions_snoozed', 'customactions_dismissed', 'behaviors_total',
            'engagement_15_days', 'engagement_30_days', 'engagement_60_days',
            'engagement_rank', 'goal_status',
            'updated_on', 'created_on', 'object_type',
        )

    def to_representation(self, obj):
        results = super().to_representation(obj)
        # The goal_status should just be a simple dict but the built-in
        # serialization wants to leave them as strings.
        results['goal_status'] = obj.goal_status
        return results

    def get_engagement_rank(self, obj):
        return max([DailyProgress.objects.engagement_rank(obj.user), 15.0])


class CategorySerializer(ObjectTypeModelSerializer):
    """A Serializer for `Category`."""
    html_description = serializers.ReadOnlyField(source="rendered_description")
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'featured', 'grouping_name', 'grouping', 'title',
            'description', 'html_description', 'packaged_content', 'icon_url',
            'image_url', 'color', 'secondary_color', 'selected_by_default',
            'object_type',
        )


class GoalSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Goal`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    categories = serializers.ReadOnlyField(source="category_ids")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Goal
        fields = (
            'id', 'sequence_order', 'title', 'description', 'html_description',
            'icon_url', 'categories', 'object_type',
        )


class BehaviorSerializer(TombstoneMixin, ObjectTypeModelSerializer):
    """A Serializer for `Behavior`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    goals = serializers.ReadOnlyField(source="goal_ids")

    class Meta:
        model = Behavior
        fields = (
            'id', 'sequence_order', 'title', 'description', 'html_description',
            'more_info', 'html_more_info', 'external_resource',
            'external_resource_name', 'icon_url', 'actions_count', 'goals',
            'object_type',
        )
        read_only_fields = ("actions_count", )


class ActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Action`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")

    class Meta:
        model = Action
        fields = (
            'id', 'sequence_order', 'title', 'description', 'html_description',
            'goals', 'behavior', 'behavior_title', 'behavior_description',
            'more_info', 'html_more_info', 'external_resource',
            'external_resource_name', 'external_resource_type',
            'notification_text', 'icon_url', 'object_type',
        )


class UserCategorySerializer(ObjectTypeModelSerializer):
    """A serializer for `UserCategory` model(s)."""
    category = SimpleCategoryField(queryset=Category.objects.all())
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

    class Meta:
        model = UserCategory
        fields = (
            'id', 'user', 'category', 'created_on', 'editable', 'object_type',
        )
        read_only_fields = ("id", "created_on")


class UserGoalSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserGoal` model."""
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    engagement_rank = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserGoal
        fields = (
            'id', 'user', 'goal', 'editable', 'primary_category',
            'engagement_15_days', 'engagement_30_days', 'engagement_60_days',
            'engagement_rank', 'weekly_completions', 'created_on', 'object_type',
        )
        read_only_fields = ("id", "created_on")

    def to_representation(self, obj):
        """Include a serialized Goal object in the result."""
        results = super().to_representation(obj)
        goal_id = results.get('goal', None)
        goal = Goal.objects.get(pk=goal_id)
        results['goal'] = GoalSerializer(goal).data
        return results

    def get_engagement_rank(self, obj):
        return max([obj.engagement_rank, 15.0])


class UserBehaviorSerializer(TombstoneMixin, ObjectTypeModelSerializer):
    """A Serializer for the `UserBehavior` model."""
    editable = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserBehavior
        fields = (
            'id', 'user', 'behavior', 'created_on', 'editable',
            'object_type',
        )
        read_only_fields = ("id", "created_on", )

    def __init__(self, *args, **kwargs):
        self.parents = kwargs.pop("parents", False)
        super().__init__(*args, **kwargs)

    def get_editable(self, obj):
        return True  # XXX Temporarily enabling this for everyone.

    def to_representation(self, obj):
        """Include a serialized Behavior object in the result."""
        results = super().to_representation(obj)
        behavior_id = results.get('behavior', None)
        behavior = Behavior.objects.get(pk=behavior_id)
        results['behavior'] = BehaviorSerializer(behavior).data
        return results


class UserActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserAction` model."""
    trigger = CustomTriggerField(
        queryset=Trigger.objects.custom(),
        required=False,
    )
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    next_reminder = ReadOnlyDatetimeField()
    primary_usergoal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserAction
        fields = (
            'id', 'user', 'action', 'trigger', 'next_reminder',
            'editable', 'created_on', 'goal_title', 'goal_icon',
            'userbehavior_id', 'primary_goal', 'primary_usergoal',
            'primary_category', 'object_type',
        )
        read_only_fields = ("id", "created_on", 'userbehavior_id', 'goal')

    def __init__(self, *args, **kwargs):
        self.parents = kwargs.pop("parents", False)
        super().__init__(*args, **kwargs)

    def get_primary_usergoal(self, obj):
        result = obj.get_primary_usergoal(only='id')
        if result:
            return result.id
        return None

    def to_representation(self, obj):
        """Replace the `action` ID with a serialized Action object."""
        results = super().to_representation(obj)
        results['action'] = ActionSerializer(obj.action).data
        return results

    def create(self, validated_data):
        """Handle the primary_goal field correctly; We use `get_primary_goal`
        to populate it's method, but when creating an instance that's not a
        valid argument for UserAction.objects.create.

        """
        primary_goal = validated_data.pop("get_primary_goal", None)
        if primary_goal:
            validated_data['primary_goal'] = primary_goal
        return super().create(validated_data)
