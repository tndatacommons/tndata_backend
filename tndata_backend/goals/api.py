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


class GoalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Goal.objects.all()
    serializer_class = serializers.GoalSerializer

    def get_queryset(self):
        if 'category' in self.request.GET:
            self.queryset = self.queryset.filter(
                categories__id=self.request.GET['category']
            )
        return self.queryset


class TriggerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Trigger.objects.all()
    serializer_class = serializers.TriggerSerializer


class BehaviorSequenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.BehaviorSequence.objects.all()
    serializer_class = serializers.BehaviorSequenceSerializer

    def get_queryset(self):
        if 'category' in self.request.GET:
            self.queryset = self.queryset.filter(
                categories__id=self.request.GET['category']
            )
        if 'goal' in self.request.GET:
            self.queryset = self.queryset.filter(
                goals__id=self.request.GET['goal']
            )
        return self.queryset


class BehaviorActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.BehaviorAction.objects.all()
    serializer_class = serializers.BehaviorActionSerializer

    def get_queryset(self):
        if 'category' in self.request.GET:
            self.queryset = self.queryset.filter(
                sequence__categories__id=self.request.GET['category']
            )
        if 'goal' in self.request.GET:
            self.queryset = self.queryset.filter(
                sequence__goals__id=self.request.GET['goal']
            )
        if 'sequence' in self.request.GET:
            self.queryset = self.queryset.filter(
                sequence__id=self.request.GET['sequence']
            )
        return self.queryset
