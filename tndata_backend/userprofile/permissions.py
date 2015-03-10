from rest_framework import permissions


class IsSelf(permissions.BasePermission):
    """This permission checks that the authenticated user is the owner for a
    User or UserProfile instance.

    NOTE: the default permissions require authentication

    """

    def has_object_permission(self, request, view, obj):
        try:
            return obj.user == request.user
        except AttributeError:
            return obj == request.user
