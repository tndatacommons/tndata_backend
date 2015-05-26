from django.contrib.auth import get_user_model
from rest_framework import serializers
from . models import (
    Action,
    Behavior,
    BehaviorProgress,
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


User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """A Serializer for `Category`."""
    goals = GoalListField(many=True, read_only=True)
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'title', 'title_slug', 'description',
            'goals', 'icon_url', 'image_url', 'color',
        )


class GoalSerializer(serializers.ModelSerializer):
    """A Serializer for `Goal`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    categories = CategoryListField(many=True, read_only=True)

    class Meta:
        model = Goal
        fields = (
            'id', 'title', 'title_slug', 'description', 'outcome',
            'icon_url', 'categories',
        )


class TriggerSerializer(serializers.ModelSerializer):
    """A Serializer for `Trigger`."""
    recurrences_display = serializers.ReadOnlyField(source='recurrences_as_text')

    class Meta:
        model = Trigger
        fields = (
            'id', 'name', 'name_slug', 'trigger_type', 'time', 'location',
            'recurrences', 'recurrences_display', 'next',
        )


class BehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for `Behavior`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")
    goals = GoalListField(many=True, read_only=True)

    class Meta:
        model = Behavior
        fields = (
            'id', 'title', 'title_slug', 'description', 'more_info',
            'external_resource', 'default_trigger', 'notification_text',
            'icon_url', 'image_url', 'goals',
        )


class BehaviorProgressSerializer(serializers.ModelSerializer):
    """A Serializer for `BehaviorProgress`."""

    class Meta:
        model = BehaviorProgress
        fields = (
            'id', 'user', 'user_behavior', 'status', 'status_display',
            'reported_on',
        )


class ActionSerializer(serializers.ModelSerializer):
    """A Serializer for `Action`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")
    behavior = SimpleBehaviorField(read_only=True)

    class Meta:
        model = Action
        fields = (
            'id', 'behavior', 'sequence_order', 'title', 'title_slug',
            'title', 'description', 'more_info', 'external_resource',
            'default_trigger', 'notification_text', 'icon_url', 'image_url',
        )


class UserGoalSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserGoal` model."""
    user_categories = SimpleCategoryField(
        source="get_user_categories",
        many=True,
        read_only=True,
    )
    goal = SimpleGoalField(queryset=Goal.objects.none())

    class Meta:
        model = UserGoal
        fields = (
            'id', 'user', 'goal', 'user_categories', 'created_on',
            'progress_value',
        )
        read_only_fields = ("id", "created_on")


class UserBehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserBehavior` model."""
    user_goals = SimpleGoalField(
        source="get_user_goals",
        many=True,
        read_only=True,
    )
    behavior = SimpleBehaviorField(queryset=Behavior.objects.all())

    class Meta:
        model = UserBehavior
        fields = ('id', 'user', 'behavior', 'user_goals', 'created_on')
        read_only_fields = ("id", "created_on", )


class UserActionSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserAction` model."""
    action = SimpleActionField(queryset=Action.objects.all())

    class Meta:
        model = UserAction
        fields = ('id', 'user', 'action', 'created_on')
        read_only_fields = ("id", "created_on", )


class UserCategorySerializer(serializers.ModelSerializer):
    """A serializer for `UserCategory` model(s)."""
    category = SimpleCategoryField(queryset=Category.objects.all())
    user_goals = SimpleGoalField(source="get_user_goals", many=True, read_only=True)

    class Meta:
        model = UserCategory
        fields = ('id', 'user', 'category', 'user_goals', 'created_on')
        read_only_fields = ("id", "created_on", )
