from rest_framework import serializers

from ..models import (
    Action,
    Behavior,
    Category,
    Goal,
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
from .base import ObjectTypeModelSerializer

# XXX: Things we don't want to change from v1
from .v1 import (  # flake8: noqa
    BehaviorProgressSerializer,
    CustomActionSerializer,
    CustomGoalSerializer,
    SearchSerializer,
    GoalProgressSerializer,
    PackageEnrollmentSerializer,
    ReadOnlyUserGoalSerializer,
    ReadOnlyUserActionSerializer,
    TriggerSerializer,
)


class CategorySerializer(ObjectTypeModelSerializer):
    """A Serializer for `Category`."""
    html_description = serializers.ReadOnlyField(source="rendered_description")
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'title', 'description', 'html_description',
            'packaged_content', 'icon_url', 'image_url', 'color',
            'secondary_color', 'object_type',
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
            'id', 'title', 'description', 'html_description', 'outcome',
            'icon_url', 'categories', 'behaviors_count', 'object_type',
        )


class BehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Behavior`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    goals = serializers.ReadOnlyField(source="goal_ids")

    class Meta:
        model = Behavior
        fields = (
            'id', 'title', 'description', 'html_description', 'more_info',
            'html_more_info', 'external_resource', 'external_resource_name',
            'icon_url', 'actions_count', 'goals', 'object_type',
        )
        read_only_fields = ("actions_count", )


class ActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Action`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    default_trigger = serializers.ReadOnlyField(source='serialized_default_trigger')

    class Meta:
        model = Action
        fields = (
            'id', 'behavior', 'sequence_order', 'title', 'description',
            'html_description', 'more_info', 'html_more_info',
            'external_resource', 'external_resource_name', 'default_trigger',
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
    progress = GoalProgressSerializer(read_only=True)
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    primary_category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserGoal
        fields = (
            'id', 'user', 'goal', 'progress', 'editable', 'created_on',
             'primary_category', 'object_type',
        )
        read_only_fields = ("id", "created_on")

    def to_representation(self, obj):
        """Include a serialized Goal object in the result."""
        results = super().to_representation(obj)
        goal_id = results.get('goal', None)
        goal = Goal.objects.get(pk=goal_id)
        results['goal'] = GoalSerializer(goal).data
        return results

    def get_primary_category(self, obj):
        cat = obj.get_primary_category()
        if cat:
            return cat.id
        return None


class UserBehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserBehavior` model."""
    progress = BehaviorProgressSerializer(read_only=True)
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

    class Meta:
        model = UserBehavior
        fields = (
            'id', 'user', 'behavior', 'progress', 'created_on', 'editable',
            'object_type',
        )
        read_only_fields = ("id", "created_on", )

    def to_representation(self, obj):
        """Include a serialized Behavior object in the result."""
        results = super().to_representation(obj)
        behavior_id = results.get('behavior', None)
        behavior = Behavior.objects.get(pk=behavior_id)
        results['behavior'] = GoalSerializer(behavior).data
        return results


class UserActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserAction` model."""
    action = ActionSerializer()
    trigger = CustomTriggerField(
        queryset=Trigger.objects.custom(),
        required=False,
    )
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    next_reminder = serializers.ReadOnlyField(source='next')
    primary_category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserAction
        fields = (
            'id', 'user', 'action', 'trigger', 'next_reminder',
            'editable', 'created_on', 'primary_goal', 'primary_category',
            'object_type',
        )
        read_only_fields = ("id", "created_on", )

    def create(self, validated_data):
        """Handle the primary_goal field correctly; We use `get_primary_goal`
        to populate it's method, but when creating an instance that's not a
        valid argument for UserAction.objects.create.

        """
        primary_goal = validated_data.pop("get_primary_goal", None)
        if primary_goal:
            validated_data['primary_goal'] = primary_goal
        return super().create(validated_data)

    def get_primary_category(self, obj):
        cat = obj.get_primary_category()
        if cat:
            return cat.id
        return None
