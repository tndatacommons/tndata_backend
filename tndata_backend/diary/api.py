from rest_framework import permissions, serializers, viewsets
from . import models


class IsEntryOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class EntrySerializer(serializers.ModelSerializer):
    """A Serializer for `diary.models.Entry`."""
    rank_display = serializers.CharField(source='rank_display', read_only=True)
    class Meta:
        model = models.Entry
        fields = ('id', 'user', 'rank', 'rank_display', 'notes', 'submitted_on')


class EntryViewSet(viewsets.ModelViewSet):
    queryset = models.Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [IsEntryOwner]  # NOTE: default perms require authentication

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def pre_save(self, obj):
        # TODO: Figure out a better way to assign default ownership when
        # objects are created.
        obj.user = self.request.user
