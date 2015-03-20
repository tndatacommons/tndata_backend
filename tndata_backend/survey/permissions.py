from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """This permission checks that the authenticated user is the owner a given
    object. For this to work, the object MUST have a `user` attribute.

    """

    def has_object_permission(self, request, view, obj):
        try:
            return request.user.is_authenticated() and obj.user == request.user
        except AttributeError:
            return False
