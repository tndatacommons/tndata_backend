from rest_framework import mixins, permissions, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)

from . import models
from . import serializers


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class GCMMessageViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """This endpoint allows clients to create a message to be sent through
    [Google Cloud Messaging](https://developer.android.com/google/gcm).

    To create a message, you must POST the following information to
    `/api/notifications/`:

    * `registration_id`: This is the device's registration ID. For more info,
      see the [Register for GCM](https://developer.android.com/google/gcm/client.html#sample-register) section in the android developer documentation.
    * `content`: The JSON-encoded message.
    * `deliver_on`: The date/time on which the message should be delivered, e.g
      `2015-12-24 23:59`.
    * `expire_on`: (optional) A date/time on which this message should be
      expired (deleted from our system).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GCMMessage.objects.all()
    serializer_class = serializers.GCMMessageSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        # We're creating a single items.
        request.data['user'] = request.user.id
        return super(GCMMessageViewSet, self).create(request, *args, **kwargs)
