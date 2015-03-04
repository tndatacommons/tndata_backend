from rest_framework import serializers
from . models import (
    BehaviorAction,
    BehaviorSequence,
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
            'categories', 'icon_url',
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


class BehaviorSequenceSerializer(serializers.ModelSerializer):
    """A Serializer for `BehaviorSequence`."""
    icon_url = serializers.Field(source="get_absolute_icon")
    image_url = serializers.Field(source="get_absolute_image")

    class Meta:
        model = BehaviorSequence
        fields = (
            'id', 'name', 'name_slug', 'title', 'description', 'case', 'outcome',
            'narrative_block', 'external_resource', 'default_trigger',
            'notification_text', 'source_notes', 'source_link', 'informal_list',
            'icon_url', 'image_url', 'goals',
        )
        depth = 2


class BehaviorActionSerializer(serializers.ModelSerializer):
    """A Serializer for `BehaviorAction`."""
    icon_url = serializers.Field(source="get_absolute_icon")
    image_url = serializers.Field(source="get_absolute_image")

    class Meta:
        model = BehaviorAction
        fields = (
            'id', 'sequence', 'sequence_order', 'name', 'name_slug',
            'title', 'description', 'case', 'outcome', 'narrative_block',
            'external_resource', 'default_trigger', 'notification_text',
            'source_notes', 'source_link', 'icon_url', 'image_url',
        )
        depth = 2
