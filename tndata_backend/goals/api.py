import re
from rest_framework import fields, permissions, serializers, viewsets
from . import models


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class TextArrayField(fields.ModelField):
    """A Simple serializer field for a djorm_pgarray.fields.TextArrayField.

    Usage: Include on a Serializer subclass, and specify the `model_field`. This
    will be used to convert input back to a python object.

    """
    def from_native(self, value):
        # Input values may be a string that looks anything like:
        #
        #   '["one", "two", "three"]'
        #   '[one, two, three]'
        #   'one, two, three'
        #
        values = re.sub(r'[\[|\]|"|\']', '', value).split(',')
        values = [v.strip() for v in values]
        return self.model_field.field.to_python(values)

    def field_to_native(self, obj, field_name):
        return getattr(obj, field_name, None)


class CategorySerializer(serializers.ModelSerializer):
    """A Serializer for `Category`."""

    class Meta:
        model = models.Category
        fields = ('id', 'order', 'name', 'description')


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = CategorySerializer


class InterestSerializer(serializers.ModelSerializer):
    """A Serializer for `Interest`."""
    max_neef_tags = TextArrayField(model_field=models.Interest.max_neef_tags)

    class Meta:
        model = models.Interest
        fields = (
            'id', 'order', 'name', 'description', 'categories',
            'max_neef_tags', 'sdt_major'
        )
        depth = 1


class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Interest.objects.all()
    serializer_class = InterestSerializer


class ActionSerializer(serializers.ModelSerializer):
    """A Serializer for `Action`."""
    interests = InterestSerializer()

    class Meta:
        model = models.Action
        fields = (
            'id', 'interests', 'order', 'name', 'summary', 'description',
            'default_reminder_time', 'default_reminder_frequency',
        )
        depth = 2


class ActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Action.objects.all()
    serializer_class = ActionSerializer


class CustomReminderSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.CustomReminder`."""

    class Meta:
        model = models.CustomReminder
        fields = ('id', 'user', 'action', 'time', 'frequency')
        depth = 1


class CustomReminderViewSet(viewsets.ModelViewSet):
    queryset = models.CustomReminder.objects.all()
    serializer_class = CustomReminderSerializer
    permission_classes = [IsOwner]  # NOTE: default perms require authentication


class SelectedActionSerializer(serializers.ModelSerializer):
    """A Serializer for `SelectedAction`."""

    class Meta:
        model = models.SelectedAction
        fields = ('id', 'user', 'action', 'date_selected')
        depth = 1


class SelectedActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.SelectedAction.objects.all()
    serializer_class = SelectedActionSerializer
    permission_classes = [IsOwner]  # NOTE: default perms require authentication


class ActionTakenSerializer(serializers.ModelSerializer):
    """A Serializer for `ActionTaken`."""

    class Meta:
        model = models.ActionTaken
        fields = ('id', 'user', 'selected_action', 'date_completed')
        depth = 2


class ActionTakenViewSet(viewsets.ModelViewSet):
    queryset = models.ActionTaken.objects.all()
    serializer_class = ActionTakenSerializer
    permission_classes = [IsOwner]  # NOTE: default perms require authentication
