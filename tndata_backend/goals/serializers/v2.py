from django.conf import settings
from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer

from ..models import (
    Action,
    Behavior,
    Category,
    DailyProgress,
    Goal,
    Trigger,
    UserAction,
    UserGoal,
    UserBehavior,
    UserCategory,
)
from ..serializer_fields import (
    CustomTriggerField,
    ReadOnlyDatetimeField,
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
    ReadOnlyUserGoalSerializer,
    ReadOnlyUserActionSerializer,
    TriggerSerializer,
)


class DailyProgressSerializer(ObjectTypeModelSerializer):

    class Meta:
        model = DailyProgress
        fields = (
            'id', 'user', 'actions_total', 'actions_completed', 'actions_snoozed',
            'actions_dismissed', 'customactions_total', 'customactions_completed',
            'customactions_snoozed', 'customactions_dismissed', 'behaviors_total',
            'behaviors_status', 'goal_status', 'updated_on', 'created_on',
            'object_type',
        )

    def to_representation(self, obj):
        results = super().to_representation(obj)
        # The goal_status and behavior_status should just be simple dicts
        # but the built-in serialization wants to leave them as strings.
        results['behaviors_status'] = obj.behaviors_status
        results['goal_status'] = obj.goal_status
        return results


class CategorySerializer(ObjectTypeModelSerializer):
    """A Serializer for `Category`."""
    html_description = serializers.ReadOnlyField(source="rendered_description")
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'featured', 'title', 'description',
            'html_description', 'packaged_content', 'icon_url', 'image_url',
            'color', 'secondary_color', 'selected_by_default', 'object_type',
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
            'outcome', 'icon_url', 'categories', 'behaviors_count',
            'object_type',
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
            'id', 'behavior', 'behavior_title', 'behavior_description',
            'sequence_order', 'title', 'description', 'html_description',
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

    class Meta:
        model = UserGoal
        fields = (
            'id', 'user', 'goal', 'editable', 'created_on',
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


class UserBehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserBehavior` model."""
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

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

    def include_parent_objects(self, results):
        if self.parents:
            # Include the parent UserCategory object.
            uc = UserCategory.objects.filter(
                user__pk=results['user'],
                category__pk=self.parents.get('category')
            ).first()
            results['parent_usercategory'] = UserCategorySerializer(uc).data

            # Include the parent UserGoal object.
            ug = UserGoal.objects.filter(
                user__pk=results['user'],
                goal__pk=self.parents.get('goal')
            ).first()
            results['parent_usergoal'] = UserGoalSerializer(ug).data
        return results

    def to_representation(self, obj):
        """Include a serialized Behavior object in the result."""
        results = super().to_representation(obj)
        behavior_id = results.get('behavior', None)
        behavior = Behavior.objects.get(pk=behavior_id)
        results['behavior'] = BehaviorSerializer(behavior).data
        results = self.include_parent_objects(results)
        return results


class UserActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserAction` model."""
    trigger = CustomTriggerField(
        queryset=Trigger.objects.custom(),
        required=False,
    )
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    next_reminder = ReadOnlyDatetimeField(source='next')

    class Meta:
        model = UserAction
        fields = (
            'id', 'user', 'action', 'trigger', 'next_reminder',
            'editable', 'created_on', 'goal_title', 'userbehavior_id',
            'primary_goal', 'primary_category', 'object_type',
        )
        read_only_fields = ("id", "created_on", 'userbehavior_id', )

    def __init__(self, *args, **kwargs):
        self.parents = kwargs.pop("parents", False)
        super().__init__(*args, **kwargs)

    def include_parent_objects(self, results):
        if self.parents:
            # Include the parent UserCategory object.
            uc = UserCategory.objects.filter(
                user__pk=results['user'],
                category__pk=self.parents.get('category')
            ).first()
            results['parent_usercategory'] = UserCategorySerializer(uc).data

            # Include the parent UserGoal object.
            ug = UserGoal.objects.filter(
                user__pk=results['user'],
                goal__pk=self.parents.get('goal')
            ).first()
            results['parent_usergoal'] = UserGoalSerializer(ug).data

            # Include the parent UserBehavior object.
            ub = UserBehavior.objects.filter(
                user__pk=results['user'],
                behavior__pk=self.parents.get('behavior')
            ).first()
            results['parent_userbehavior'] = UserBehaviorSerializer(ub).data
        return results

    def to_representation(self, obj):
        """Include a serialized Action object in the result."""
        results = super().to_representation(obj)
        action_id = results.get('action', None)
        action = Action.objects.get(pk=action_id)
        results['action'] = ActionSerializer(action).data
        results = self.include_parent_objects(results)
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
