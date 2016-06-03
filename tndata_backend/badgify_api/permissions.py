from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """This permission checks that the authenticated user is the owner of the
    specified objets in the queryset. This allows users to see only their
    own data.

    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
