from rest_framework import serializers
from . models import (
    Action,
    Behavior,
    Category,
    Goal,
    Trigger,
)


class GoalListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Goal
    information on a Category."""
    def to_native(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'subtitle': value.subtitle,
            'description': value.description,
            'outcome': value.outcome,
            'icon_url': value.get_absolute_icon(),
        }


class CategoryListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Categories."""
    def to_native(self, value):
        return {
            'id': value.id,
            'order': value.order,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'icon_url': value.get_absolute_icon(),
        }


class CategorySerializer(serializers.ModelSerializer):
    """A Serializer for `Category`."""
    goals = GoalListField(many=True)
    icon_url = serializers.Field(source="get_absolute_icon")

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'title', 'title_slug', 'description',
            'goals', 'icon_url',
        )
        depth = 1


class GoalSerializer(serializers.ModelSerializer):
    """A Serializer for `Goal`."""
    icon_url = serializers.Field(source="get_absolute_icon")
    categories = CategoryListField(many=True)

    class Meta:
        model = Goal
        fields = (
            'id', 'title', 'title_slug', 'subtitle', 'description', 'outcome',
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


class SimpleBehaviorField(serializers.RelatedField):
    """A simplified representation of a `BehaviorSequence`."""
    def to_native(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'narrative_block': value.narrative_block,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
        }


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
