from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)
from rest_framework.response import Response

from . import models
from . import serializers


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class GCMDeviceViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    """This endpoint allows an Android client to register a User's device so
    for notifications via
    [Google Cloud Messaging](https://developer.android.com/google/gcm).

    To create a message, you must POST the following information to
    `/api/notifications/devices`:

    * `registration_id`: This is the device's registration ID. For more info,
      see the [Register for GCM](https://developer.android.com/google/gcm/client.html#sample-register) section in the android developer documentation.
    * `device_name`: (optional) a name for the device
    * `is_active`: (optional) Defaults to True; whether or not the device accepts
      notifications.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GCMDevice.objects.all()
    serializer_class = serializers.GCMDeviceSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""

        if request.user.is_authenticated():
            qs = models.GCMDevice.objects.filter(
                user=request.user,
                registration_id=request.data.get('registration_id')
            )
            if qs.exists():
                # No need to do anything.
                return Response(None, status=status.HTTP_304_NOT_MODIFIED)

            request.data['user'] = request.user.id
        return super(GCMDeviceViewSet, self).create(request, *args, **kwargs)


class GCMMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """This endpoint allows an Android client to list notifications scheduled
    to be delivered through
    [Google Cloud Messaging](https://developer.android.com/google/gcm).

    NOTE: This payload has a limit of 4096 bytes.

    ## Registration

    Devices should be registered at the
    [/api/notifications/devices/](/api/notifications/devices/) endpoint.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GCMMessage.objects.all()
    serializer_class = serializers.GCMMessageSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)
