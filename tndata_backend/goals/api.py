from rest_framework import permissions, serializers, viewsets
from . import models


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class GoalSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.Goal`."""

    class Meta:
        model = models.Goal
        fields = ('id', 'rank', 'name', 'explanation', 'max_neef_tags', 'sdt_major')


class GoalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Goal.objects.all()
    serializer_class = GoalSerializer


class BehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.Behavior`."""

    class Meta:
        model = models.Behavior
        fields = ('id', 'goal', 'name', 'summary', 'description')


class BehaviorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Behavior.objects.all()
    serializer_class = BehaviorSerializer


class BehaviorStepSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.BehaviorStep`."""

    class Meta:
        model = models.BehaviorStep
        fields = (
            'id', 'goal', 'behavior', 'name', 'description', 'reminder_type',
            'default_time', 'default_repeat', 'default_location',
        )


class BehaviorStepViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.BehaviorStep.objects.all()
    serializer_class = BehaviorStepSerializer


class CustomReminderSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.CustomReminder`."""

    class Meta:
        model = models.CustomReminder
        fields = (
            'id', 'user', 'behavior_step', 'reminder_type',
            'time', 'repeat', 'location',
        )


class CustomReminderViewSet(viewsets.ModelViewSet):
    queryset = models.CustomReminder.objects.all()
    serializer_class = CustomReminderSerializer
    permission_classes = [IsOwner]  # NOTE: default perms require authentication


class ChosenBehaviorSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.ChosenBehavior`."""

    class Meta:
        model = models.ChosenBehavior
        fields = ('id', 'user', 'goal', 'behavior', 'date_selected')


class ChosenBehaviorViewSet(viewsets.ModelViewSet):
    queryset = models.ChosenBehavior.objects.all()
    serializer_class = ChosenBehaviorSerializer
    permission_classes = [IsOwner]  # NOTE: default perms require authentication


class CompletedBehaviorStepSerializer(serializers.ModelSerializer):
    """A Serializer for `goals.models.CompletedBehaviorStep`."""

    class Meta:
        model = models.CompletedBehaviorStep
        fields = ('id', 'user', 'goal', 'behavior', 'behavior_step', 'date_completed')


class CompletedBehaviorStepViewSet(viewsets.ModelViewSet):
    queryset = models.CompletedBehaviorStep.objects.all()
    serializer_class = CompletedBehaviorStepSerializer
    permission_classes = [IsOwner]  # NOTE: default perms require authentication
