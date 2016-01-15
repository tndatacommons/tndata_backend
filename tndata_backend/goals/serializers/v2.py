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
    behaviors_count = serializers.SerializerMethodField()
    primary_category = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Goal
        fields = (
            'id', 'title', 'description', 'html_description', 'outcome',
            'icon_url', 'primary_category', 'categories', 'behaviors_count',
            'object_type',
        )

    def get_categories(self, obj):
        """Return a list of parent category IDs."""
        return list(obj.categories.values_list('id', flat=True))

    def get_behaviors_count(self, obj):
        """Return the number of child Behaivors for the given Goal (obj)."""
        return obj.behavior_set.filter(state="published").count()

    def get_primary_category(self, obj):
        """Include a primary category object for a Goal, when possible"""
        if self.user:
            cat = obj.get_parent_category_for_user(self.user)
            return CategorySerializer(cat).data
        return None


class BehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Behavior`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    actions_count = serializers.SerializerMethodField()
    goals = serializers.SerializerMethodField()

    class Meta:
        model = Behavior
        fields = (
            'id', 'title', 'description', 'html_description', 'more_info',
            'html_more_info', 'external_resource', 'external_resource_name',
            'icon_url', 'actions_count', 'goals', 'object_type',
        )
        read_only_fields = ("actions_count", )

    def get_actions_count(self, obj):
        """Return the number of child Actions for the given Behavior (obj)."""
        return obj.action_set.filter(state="published").count()

    def get_goals(self, obj):
        """Return a list of parent Goal IDs"""
        return list(obj.goals.values_list("id", flat=True))


class ActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for `Action`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    default_trigger = SimpleTriggerField(read_only=True)

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
    goal = SimpleGoalField(queryset=Goal.objects.none())
    goal_progress = GoalProgressSerializer(read_only=True)
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')
    primary_category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserGoal
        fields = (
            'id', 'user', 'goal', 'goal_progress', 'progress_value',
            'editable', 'created_on', 'object_type', 'primary_category',
        )
        read_only_fields = ("id", "created_on")

    def get_primary_category(self, obj):
        cat = obj.get_primary_category()
        if cat:
            return cat.id
        return None


class UserBehaviorSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserBehavior` model."""
    behavior = SimpleBehaviorField(queryset=Behavior.objects.all())
    behavior_progress = BehaviorProgressSerializer(read_only=True)
    editable = serializers.ReadOnlyField(source='custom_triggers_allowed')

    class Meta:
        model = UserBehavior
        fields = (
            'id', 'user', 'behavior', 'behavior_progress', 'created_on',
            'editable', 'object_type',
        )
        read_only_fields = ("id", "created_on", )


class UserActionSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `UserAction` model."""
    action = SimpleActionField(queryset=Action.objects.all())
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
            'id', 'user', 'action', 'behavior', 'trigger', 'next_reminder',
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