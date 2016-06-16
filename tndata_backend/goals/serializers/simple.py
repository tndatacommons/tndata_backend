from django.contrib.auth import get_user_model
from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer

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
)
from utils.serializer_fields import ReadOnlyDatetimeField


User = get_user_model()


class SimpleCategorySerializer(ObjectTypeModelSerializer):
    """A Serializer for `Category` without related fields."""
    html_description = serializers.ReadOnlyField(source="rendered_description")
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")
    featured = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'featured', 'title', 'title_slug', 'description',
            'html_description', 'packaged_content', 'icon_url', 'image_url',
            'color', 'secondary_color', 'object_type',
        )


class SimpleGoalSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Goal` without related models' data."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    primary_category = serializers.SerializerMethodField()  # NOTE: id only

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Goal
        fields = (
            'id', 'sequence_order', 'title', 'title_slug', 'description',
            'html_description', 'outcome', 'icon_url', 'primary_category',
            'object_type',
        )

    def get_primary_category(self, obj):
        """Include a primary category id for a goal, when possible"""
        if self.user:
            cat = obj.get_parent_category_for_user(self.user)
            return SimpleCategorySerializer(cat).data
        return None


class SimpleBehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Behavior` instances without related fields."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    actions_count = serializers.SerializerMethodField()

    class Meta:
        model = Behavior
        fields = (
            'id', 'sequence_order', 'title', 'title_slug', 'description',
            'html_description', 'more_info', 'html_more_info',
            'external_resource', 'external_resource_name', 'icon_url',
            'actions_count', 'object_type',
        )
        read_only_fields = ("actions_count", )

    def get_actions_count(self, obj):
        """Return the number of child Actions for the given Behavior (obj)."""
        return obj.action_set.filter(state="published").count()


class SimpleUserGoalSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserGoal` model containing only goal data"""
    goal = SimpleGoalField(queryset=Goal.objects.none())
    custom_triggers_allowed = serializers.ReadOnlyField()
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

    class Meta:
        model = UserGoal
        fields = (
            'id', 'user', 'goal', 'created_on', 'custom_triggers_allowed',
            'editable', 'object_type'
        )
        read_only_fields = ("id", "created_on")


class SimpleUserBehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserBehavior` model with *only* Behavior data."""
    behavior = SimpleBehaviorField(queryset=Behavior.objects.all())
    custom_triggers_allowed = serializers.ReadOnlyField()
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

    class Meta:
        model = UserBehavior
        fields = (
            'id', 'user', 'behavior', 'created_on',
            'custom_triggers_allowed', 'editable', 'object_type'
        )
        read_only_fields = ("id", "created_on", )

    def get_user_actions_count(self, obj):
        """Return the number of user-selected actions that are children of
        this Behavior."""
        return obj.get_actions().count()


class SimpleUserActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserAction` model with *just* Action data."""
    action = SimpleActionField(queryset=Action.objects.all())
    primary_goal = serializers.SerializerMethodField(required=False)
    custom_trigger = CustomTriggerField(
        queryset=Trigger.objects.custom(),
        required=False
    )
    custom_triggers_allowed = serializers.ReadOnlyField()
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    next_reminder = ReadOnlyDatetimeField(source='next')

    class Meta:
        model = UserAction
        fields = (
            'id', 'user', 'action', 'primary_goal', 'custom_trigger',
            'next_reminder', 'custom_triggers_allowed', 'editable',
            'created_on', 'object_type',
        )
        read_only_fields = ("id", "created_on", )

    def get_primary_goal(self, obj):
        goal = obj.get_primary_goal()
        if goal is not None:
            return goal.id
        return None


class SimpleUserCategorySerializer(ObjectTypeModelSerializer):
    """A serializer for `UserCategory` model(s) with *only* category data."""
    category = SimpleCategoryField(queryset=Category.objects.all())
    custom_triggers_allowed = serializers.ReadOnlyField()
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

    class Meta:
        model = UserCategory
        fields = (
            'id', 'user', 'category', 'created_on',
            'custom_triggers_allowed', 'editable', 'object_type',
        )
        read_only_fields = ("id", "created_on")
