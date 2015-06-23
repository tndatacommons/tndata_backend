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
    CustomTriggerField,
    GoalListField,
    SimpleActionField,
    SimpleBehaviorField,
    SimpleCategoryField,
    SimpleGoalField,
    SimpleTriggerField,
)


User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """A Serializer for `Category`."""
    goals = GoalListField(many=True, read_only=True)
    html_description = serializers.ReadOnlyField(source="rendered_description")
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'title', 'title_slug', 'description',
            'html_description', 'goals', 'icon_url', 'image_url', 'color',
        )


class GoalSerializer(serializers.ModelSerializer):
    """A Serializer for `Goal`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    categories = CategoryListField(many=True, read_only=True)
    html_description = serializers.ReadOnlyField(source="rendered_description")

    class Meta:
        model = Goal
        fields = (
            'id', 'title', 'title_slug', 'description', 'html_description',
            'outcome', 'icon_url', 'categories',
        )


class TriggerSerializer(serializers.ModelSerializer):
    """A Serializer for `Trigger`s.  Includes user information, though
    that may be null for the set of defulat (non-custom) triggers."""
    recurrences_display = serializers.ReadOnlyField(source='recurrences_as_text')

    class Meta:
        model = Trigger
        fields = (
            'id', 'user', 'name', 'name_slug', 'trigger_type', 'time', 'location',
            'recurrences', 'recurrences_display', 'next',
        )
        read_only_fields = ("id", "name_slug", "next")


class CustomTriggerSerializer(serializers.Serializer):
    """This serializer is used to create custom triggers that are associated
    with other models (e.g. UserBehaviors and UserActions). It accepts input
    that differs from a trigger:

    * user_id: An integer representing the ID of the user who *owns* the trigger

    Optional fields:

    * name: The name of the trigger; This must be unique and it's up to you
      to make sure that happens.
    * time: A string representing a time (naive; will be saved at UTC when
      creating the trigger)
    * date: A string representing a date (yyyy-mm-dd)
    * rrule: An RFC2445 formatted unicode string describing the recurrence.

    Calling this serializer's `save` method will either update or create
    a `Trigger` instance.

    Usage:

    To create a trigger from a dict of data:

        CustomTriggerSerializer(data={...})

    To update a trigger from a dict of data:

        CustomTriggerSerializer(trigger_instance, data={...})

    """
    user_id = serializers.IntegerField()
    name = serializers.CharField()
    time = serializers.TimeField(required=False)
    date = serializers.DateField(format="%Y-%m-%d", required=False)
    rrule = serializers.CharField(required=False)

    def is_valid(self, *args, **kwargs):
        """Ensure that the user for the given user_id actually exists."""
        valid = super().is_valid(*args, **kwargs)
        if valid:
            # Check to see if the user exists, and if so, keep a private
            # instance for them.
            try:
                self._user = User.objects.get(pk=self.validated_data['user_id'])
            except User.DoesNotExist:
                valid = False
                self._user = None
        return valid

    def create(self, validated_data):
        return Trigger.objects.create_for_user(
            user=self._user,
            name=validated_data['name'],
            time=validated_data.get('time'),
            date=validated_data.get('date'),
            rrule=validated_data.get('rrule')
        )

    def update(self, instance, validated_data):
        instance.time = self.validated_data.get('time', instance.time)
        instance.trigger_date = self.validated_data.get(
            'date', instance.trigger_date
        )
        instance.recurrences = self.validated_data.get(
            'rrule', instance.recurrences
        )
        instance.save()
        return instance


class BehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for `Behavior`."""
    icon_url = serializers.ReadOnlyField(source="get_absolute_icon")
    image_url = serializers.ReadOnlyField(source="get_absolute_image")
    goals = GoalListField(many=True, read_only=True)
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")

    class Meta:
        model = Behavior
        fields = (
            'id', 'title', 'title_slug', 'description', 'html_description',
            'more_info', 'html_more_info', 'external_resource', 'default_trigger',
            'notification_text', 'icon_url', 'image_url', 'goals',
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
    html_description = serializers.ReadOnlyField(source="rendered_description")
    html_more_info = serializers.ReadOnlyField(source="rendered_more_info")
    default_trigger = SimpleTriggerField(read_only=True)

    class Meta:
        model = Action
        fields = (
            'id', 'behavior', 'sequence_order', 'title', 'title_slug',
            'title', 'description', 'html_description', 'more_info',
            'html_more_info', 'external_resource', 'default_trigger',
            'notification_text', 'icon_url', 'image_url',
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
    custom_trigger = CustomTriggerField(
        queryset=Trigger.objects.custom(),
        required=False
    )

    class Meta:
        model = UserBehavior
        fields = (
            'id', 'user', 'behavior', 'custom_trigger', 'user_goals',
            'created_on',
        )
        read_only_fields = ("id", "created_on", )


class UserActionSerializer(serializers.ModelSerializer):
    """A Serializer for the `UserAction` model."""
    action = SimpleActionField(queryset=Action.objects.all())
    custom_trigger = CustomTriggerField(
        queryset=Trigger.objects.custom(),
        required=False
    )

    class Meta:
        model = UserAction
        fields = ('id', 'user', 'action', 'custom_trigger', 'created_on')
        read_only_fields = ("id", "created_on", )


class UserCategorySerializer(serializers.ModelSerializer):
    """A serializer for `UserCategory` model(s)."""
    category = SimpleCategoryField(queryset=Category.objects.all())
    user_goals = SimpleGoalField(source="get_user_goals", many=True, read_only=True)

    class Meta:
        model = UserCategory
        fields = (
            'id', 'user', 'category', 'user_goals', 'created_on', 'progress_value',
        )
        read_only_fields = ("id", "created_on", )
