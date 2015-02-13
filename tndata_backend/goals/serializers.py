from rest_framework import serializers
from . models import (
    BehaviorAction,
    BehaviorSequence,
    Category,
    Goal,
    Interest,
    Trigger,
)


class GoalListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Goal
    information on a Category."""
    def to_native(self, value):
        return {
            'id': value.id,
            'name': value.name,
            'title': value.title,
            'description': value.description,
            'outcome': value.outcome,
        }


class InterestListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Interest
    information on a Category."""
    def to_native(self, value):
        return {
            'id': value.id,
            'order': value.order,
            'name': value.name,
            'title': value.title,
            'description': value.description,
            'source_name': value.source_name,
            'source_link': value.source_link,
        }


class CategorySerializer(serializers.ModelSerializer):
    """A Serializer for `Category`."""
    goals = GoalListField(many=True)
    interests = InterestListField(many=True)

    class Meta:
        model = Category
        fields = (
            'id', 'order', 'name', 'name_slug', 'description', 'icon',
            'goals', 'interests',
        )
        depth = 1


class InterestSerializer(serializers.ModelSerializer):
    """A Serializer for `Interest`."""

    class Meta:
        model = Interest
        fields = (
            'id', 'order', 'name', 'name_slug', 'title', 'description',
            'source_name', 'source_link', 'categories',
        )
        depth = 2


class GoalSerializer(serializers.ModelSerializer):
    """A Serializer for `Goal`."""

    class Meta:
        model = Goal
        fields = (
            'id', 'name', 'name_slug', 'title', 'description', 'outcome',
            'categories', 'interests',
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

    class Meta:
        model = BehaviorSequence
        fields = (
            'id', 'name', 'name_slug', 'title', 'description', 'case', 'outcome',
            'narrative_block', 'external_resource', 'default_trigger',
            'notification_text', 'icon', 'image', 'source_notes', 'source_link',
            'categories', 'interests', 'goals', 'informal_list',
        )
        depth = 2


class BehaviorActionSerializer(serializers.ModelSerializer):
    """A Serializer for `BehaviorAction`."""

    class Meta:
        model = BehaviorAction
        fields = (
            'id', 'sequence', 'sequence_order', 'name', 'name_slug',
            'title', 'description', 'case', 'outcome', 'narrative_block',
            'external_resource', 'default_trigger', 'notification_text',
            'icon', 'image', 'source_notes', 'source_link',
        )
        depth = 2
