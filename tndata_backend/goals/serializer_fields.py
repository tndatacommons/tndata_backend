from rest_framework import serializers
from .models import Action, Behavior, Category, Goal, Trigger


def _get_object(model, pk):
    """Given a data model class and a primary key value, try to look up an
    object; If the object is not found, raise a ValidationError."""
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        msg = 'Could not find a {0} instance with a key of {1}'
        raise serializers.ValidationError(msg.format(model.__name__, pk))


class CustomTriggerField(serializers.RelatedField):
    """A field that lets us create/update a custom trigger, whenever a user
    updates a UserBehavior/UserAction."""

    def to_internal_value(self, data):
        # This is only called by by the CustomTriggerSerializer, which will
        # have already created a Trigger object (data).
        return data

    def to_representation(self, value):
        return {
            'id': value.id,
            'name': value.name,
            'name_slug': value.name_slug,
            'trigger_type': value.trigger_type,
            'time': value.time.isoformat() if value.time else None,
            'location': value.location,
            'recurrences': value.serialized_recurrences(),
            'recurrences_display': value.recurrences_as_text(),
        }


class GoalListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Goal
    information on a Category."""

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'html_description': value.rendered_description,
            'outcome': value.outcome,
            'icon_url': value.get_absolute_icon(),
        }


class CategoryListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Categories."""

    def to_representation(self, value):
        return {
            'id': value.id,
            'order': value.order,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'html_description': value.rendered_description,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
            'color': value.color,
        }


class SimpleCategoryField(serializers.RelatedField):
    """A simplified representation of a `Category`."""

    def to_internal_value(self, data):
        return _get_object(Category, data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'order': value.order,
            'description': value.description,
            'html_description': value.rendered_description,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
            'color': value.color,
            'progress_value': getattr(value, 'progress_value', 0.0),
        }


class SimpleBehaviorField(serializers.RelatedField):
    """A simplified representation of a `Behavior`."""

    def to_internal_value(self, data):
        return _get_object(Behavior, data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'html_description': value.rendered_description,
            'more_info': value.more_info,
            'html_more_info': value.rendered_more_info,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
        }


class SimpleGoalField(serializers.RelatedField):
    """A simple view of a goal."""

    def to_internal_value(self, data):
        return _get_object(Goal, data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'html_description': value.rendered_description,
            'outcome': value.outcome,
            'icon_url': value.get_absolute_icon(),
        }


class SimpleActionField(serializers.RelatedField):
    """A simple view of an action."""

    def to_internal_value(self, data):
        return _get_object(Action, data)

    def to_representation(self, value):
        default_trigger = None
        if value.default_trigger:
            default_trigger = SimpleTriggerField.to_representation(
                None,
                value.default_trigger
            )

        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'html_description': value.rendered_description,
            'more_info': value.more_info,
            'html_more_info': value.rendered_more_info,
            'outcome': value.outcome,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
            'behavior_id': value.behavior.id,
            'default_trigger': default_trigger,
        }


class SimpleTriggerField(serializers.RelatedField):
    """A Simple field for the `default_trigger` data on Actions.

    This is mean to be a read-only field.

    """

    def to_internal_value(self, data):
        return _get_object(Trigger, data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'name': value.name,
            'name_slug': value.name_slug,
            'trigger_type': value.trigger_type,
            'trigger_type_display': value.get_trigger_type_display(),
            'time': value.time,
            'location': value.location,
            'recurrences': value.serialized_recurrences(),
            'recurrences_display': value.recurrences_as_text(),
        }
