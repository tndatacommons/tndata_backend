from rest_framework import serializers
from . models import (
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

from . serializer_fields import (
    CategoryListField,
    GoalListField,
    SimpleActionField,
    SimpleBehaviorField,
    SimpleCategoryField,
    SimpleGoalField,
)


class CategorySerializer(serializers.ModelSerializer):
    """A Serializer for `Category`."""
    goals = GoalListField(many=True)
    icon_url = serializers.Field(source="get_absolute_icon")
    image_url = serializers.Field(source="get_absolute_image")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'title', 'title_slug', 'description',
            'goals', 'icon_url', 'image_url',
        )
        depth = 1


class GoalSerializer(serializers.ModelSerializer):
    """A Serializer for `Goal`."""
    icon_url = serializers.Field(source="get_absolute_icon")
    categories = CategoryListField(many=True)

    class Meta:
        model = Goal
        fields = (
            'id', 'title', 'title_slug', 'description', 'outcome',
            'icon_url', 'categories',
        )
        depth = 2


class TriggerSerializer(serializers.ModelSerializer):
    """A Serializer for `Trigger`."""

    class Meta:
        model = Trigger
        fields = (
            'id', 'name', 'name_slug', 'trigger_type', 'frequency', 'time',
            'date', 'location', 'text', 'instruction',
        )


class BehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for `Behavior`."""
    icon_url = serializers.Field(source="get_absolute_icon")
    image_url = serializers.Field(source="get_absolute_image")

    class Meta:
        model = Behavior
        fields = (
            'id', 'title', 'title_slug', 'description', 'narrative_block',
            'external_resource', 'default_trigger', 'notification_text',
            'icon_url', 'image_url', 'goals',
        )
        depth = 2


class ActionSerializer(serializers.ModelSerializer):
    """A Serializer for `Action`."""
    icon_url = serializers.Field(source="get_absolute_icon")
    image_url = serializers.Field(source="get_absolute_image")
    behavior = SimpleBehaviorField(source="behavior")

    class Meta:
        model = Action
        fields = (
            'id', 'behavior', 'sequence_order', 'title', 'title_slug',
            'title', 'description', 'narrative_block', 'external_resource',
            'default_trigger', 'notification_text', 'icon_url', 'image_url',
        )
        depth = 1


class UserGoalSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserGoal` model."""
    user_categories = SimpleCategoryField(source="get_user_categories", many=True)

    class Meta:
        model = UserGoal
        fields = ('id', 'user', 'goal', 'user_categories', 'created_on')
        read_only_fields = ("id", "created_on", )

    def to_representation(self, instance):
        """Display goal data using the SimpleGoalField representation."""
        ret = super(UserGoalSerializer, self).to_representation(instance)
        ret['goal'] = SimpleGoalField().to_representation(instance.goal)
        return ret


class UserBehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserBehavior` model."""

    class Meta:
        model = UserBehavior
        fields = ('id', 'user', 'behavior', 'created_on')
        read_only_fields = ("id", "created_on", )

    def to_representation(self, instance):
        """Display behavior data using the SimpleBehaviorField representation."""
        ret = super(UserBehaviorSerializer, self).to_representation(instance)
        ret['behavior'] = SimpleBehaviorField().to_representation(instance.behavior)
        return ret


class UserActionSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserAction` model."""

    class Meta:
        model = UserAction
        fields = ('id', 'user', 'action', 'created_on')
        read_only_fields = ("id", "created_on", )

    def to_representation(self, instance):
        """Display action data using the SimpleActionField representation."""
        ret = super(UserActionSerializer, self).to_representation(instance)
        ret['action'] = SimpleActionField().to_representation(instance.action)
        return ret


class UserCategorySerializer(serializers.ModelSerializer):
    """A serializer for `UserCategory` model(s)."""
    user_goals = SimpleGoalField(source="get_user_goals", many=True)

    class Meta:
        model = UserCategory
        fields = ('id', 'user', 'category', 'user_goals', 'created_on')
        read_only_fields = ("id", "created_on", )

    def to_representation(self, instance):
        """Display category data using the SimpleCategoryField representation."""
        ret = super(UserCategorySerializer, self).to_representation(instance)
        ret['category'] = SimpleCategoryField().to_representation(instance.category)
        return ret
