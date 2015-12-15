from rest_framework import serializers
from rest_framework.fields import empty
from .models import Action, Behavior, Category, Goal, Trigger


class EmptyFieldMixin:
    """Sets the following defaults:

    * allow_null = True
    * required = False

    And converts both None and '' values to `None` during serialization and
    deserialization.

    """
    def __init__(self, *args, **kwargs):
        """Sets the default values of `allow_null=True` and `required=False`"""
        kwargs['allow_null'] = kwargs.get('allow_null', True)
        kwargs['required'] = kwargs.get('required', False)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, value):
        """When converting to an internal value, convert any '' to None."""
        if value == "" or value is None:
            return None
        return super().to_internal_value(value)

    def to_representation(self, value):
        if value == "" or value is None:
            return None
        return super().to_representation(value)


class NullableDateField(EmptyFieldMixin, serializers.DateField):
    """A Custom DateField that allows both None and Empty String values, and
    in both cases returns a `None` value.

    This class also sets default format and input format values:

    * format: YYYY-mm-dd
    * input formats: yyyy-mm-dd, yyyy/mm/dd, or ""

    """
    format = "%Y-%m-%d",
    input_formats = ["%Y-%m-%d", "%Y/%m/%d", ""]  # 2015-06-30, 2015/06/30


class NullableTimeField(EmptyFieldMixin, serializers.TimeField):
    """A Custom TimeField that allows both None and Empty String values, and
    in both cases returns a `None` value.

    This class also sets the default format and input format values:

    * format: HH:MM
    * input formats: HH:MM, HH:MM:ss, or ""

    """
    format = "%H:%M",
    input_formats = ["%H:%M", "%H:%M:%S", ""]  # 23:30, 23:30:45, or ''


class NullableCharField(EmptyFieldMixin, serializers.CharField):
    """A Custom CharField that allows both None and Empty String values
    initially, but converts both to a `None` value.

    """
    def run_validation(self, data=empty):
        if data in ['', None]:
            return None
        return super().run_validation(data=data)


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
            'time': value.time.isoformat() if value.time else None,
            'trigger_date': value.trigger_date,
            'recurrences': value.serialized_recurrences(),
            'recurrences_display': value.recurrences_as_text(),
            'stop_on_complete': value.stop_on_complete,
            'relative_value': value.relative_value,
            'relative_units': value.relative_units,
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
            'secondary_color': value.secondary_color,
            'packaged_content': value.packaged_content,
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
            'secondary_color': value.secondary_color,
            'packaged_content': value.packaged_content,
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
            'external_resource': value.external_resource,
            'external_resource_name': value.external_resource_name,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
            'actions_count': value.action_set.filter(state="published").count(),
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
            'behaviors_count': value.behavior_set.filter(state="published").count(),
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
            'external_resource': value.external_resource,
            'external_resource_name': value.external_resource_name,
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
            'time': value.time,
            'recurrences': value.serialized_recurrences(),
            'recurrences_display': value.recurrences_as_text(),
            'stop_on_complete': value.stop_on_complete,
            'relative_value': value.relative_value,
            'relative_units': value.relative_units,
        }


class PackagedCategoryField(serializers.RelatedField):
    """A representation of a "packaged" `Category`. This is a read-only field,
    very similar to the SimpleCategoryField, but this one also includes the
    category's consent fields."""

    def to_internal_value(self, data):
        return _get_object(Category, data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'html_description': value.rendered_description,
            'consent_summary': value.consent_summary,
            'consent_more': value.consent_more,
            'html_consent_summary': value.rendered_consent_summary,
            'html_consent_more': value.rendered_consent_more,
            'packaged_content': value.packaged_content,
        }
