from rest_framework import serializers
from .models import Action, Behavior, Category, Goal


def _get_object(model, pk):
    """Given a data model class and a primary key value, try to look up an
    object; If the object is not found, raise a ValidationError."""
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        msg = 'Could not find a {0} instance with a key of {1}'
        raise serializers.ValidationError(msg.format(model.__name__, pk))


class GoalListField(serializers.RelatedField):
    """A Custom Relational Serializer field that lists a subset of Goal
    information on a Category."""

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
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
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
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
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_icon(),
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
            'narrative_block': value.narrative_block,
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
            'outcome': value.outcome,
            'icon_url': value.get_absolute_icon(),
        }


class SimpleActionField(serializers.RelatedField):
    """A simple view of an action."""

    def to_internal_value(self, data):
        return _get_object(Action, data)

    def to_representation(self, value):
        return {
            'id': value.id,
            'title': value.title,
            'title_slug': value.title_slug,
            'description': value.description,
            'outcome': value.outcome,
            'icon_url': value.get_absolute_icon(),
            'image_url': value.get_absolute_image(),
            'behavior_id': value.behavior.id,
        }


class UserActionListField(serializers.RelatedField):
    """This is used to serialize the reverse relationship between a User and
    a UserAction object; e.g. the `user.useraction_set` field.

    It uses the SimpleActionField to serialize related Action objects.
    """

    def to_representation(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'action': SimpleActionField().to_representation(value.action),
        }


class UserBehaviorListField(serializers.RelatedField):
    """This is used to serialize the reverse relationship between a User and
    a UserBehavior object; e.g. the `user.userbehavior_set` field.

    It uses the SimpleBehaviorField to serialize related Behavior objects.
    """

    def to_representation(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'behavior': SimpleBehaviorField().to_representation(value.behavior),
        }


class UserCategoryListField(serializers.RelatedField):
    """This is used to serialize the reverse relationship between a User and
    a UserCategory object; e.g. the `user.usercategory_set` field.

    It uses the SimpleCategoryField to serialize related Category objects.
    """

    def to_representation(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'category': SimpleCategoryField().to_representation(value.category),
        }


class UserGoalListField(serializers.RelatedField):
    """This is used to serialize the reverse relationship between a User and
    a UserGoal object; e.g. the `user.usergoal_set` field.

    It uses the SimpleGoalField to serialize related Goal objects.
    """

    def to_representation(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'goal': SimpleGoalField().to_representation(value.goal),
        }
