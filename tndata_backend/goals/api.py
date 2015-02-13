from rest_framework import permissions, viewsets

from . import models
from . import serializers


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer


class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Interest.objects.all()
    serializer_class = serializers.InterestSerializer


class GoalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Goal.objects.all()
    serializer_class = serializers.GoalSerializer


class TriggerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Trigger.objects.all()
    serializer_class = serializers.TriggerSerializer


class BehaviorSequenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.BehaviorSequence.objects.all()
    serializer_class = serializers.BehaviorSequenceSerializer


class BehaviorActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.BehaviorAction.objects.all()
    serializer_class = serializers.BehaviorActionSerializer


# Deprecated classes below...
#class ActionViewSet(viewsets.ReadOnlyModelViewSet):
#    queryset = models.Action.objects.all()
#    serializer_class = ActionSerializer
#
#
#class CustomReminderViewSet(viewsets.ModelViewSet):
#    queryset = models.CustomReminder.objects.all()
#    serializer_class = CustomReminderSerializer
#    permission_classes = [IsOwner]  # NOTE: default perms require authentication
#
#
#class SelectedActionViewSet(viewsets.ReadOnlyModelViewSet):
#    queryset = models.SelectedAction.objects.all()
#    serializer_class = SelectedActionSerializer
#    permission_classes = [IsOwner]  # NOTE: default perms require authentication
#
#
#class ActionTakenViewSet(viewsets.ModelViewSet):
#    queryset = models.ActionTaken.objects.all()
#    serializer_class = ActionTakenSerializer
#    permission_classes = [IsOwner]  # NOTE: default perms require authentication
