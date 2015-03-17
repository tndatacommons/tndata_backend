from rest_framework import serializers


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


class SimpleBehaviorField(serializers.RelatedField):
    """A simplified representation of a `Behavior`."""
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


class SimpleGoalField(serializers.RelatedField):
    """A simple view of a goal."""
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


class SimpleActionField(serializers.RelatedField):
    """A simple view of an action."""
    def to_native(self, value):
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
    def to_native(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'action': SimpleActionField().to_native(value.action),
        }


class UserBehaviorListField(serializers.RelatedField):
    """This is used to serialize the reverse relationship between a User and
    a UserBehavior object; e.g. the `user.userbehavior_set` field.

    It uses the SimpleBehaviorField to serialize related Behavior objects.
    """
    def to_native(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'behavior': SimpleBehaviorField().to_native(value.behavior),
        }


class UserGoalListField(serializers.RelatedField):
    """This is used to serialize the reverse relationship between a User and
    a UserGoal object; e.g. the `user.usergoal_set` field.

    It uses the SimpleGoalField to serialize related Goal objects.
    """
    def to_native(self, value):
        return {
            'id': value.id,
            'created_on': value.created_on,
            'goal': SimpleGoalField().to_native(value.goal),
        }
