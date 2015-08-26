from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

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


@receiver(user_logged_out, dispatch_uid='remove_gcm_device_on_logout')
def remove_gcm_device_on_logout(sender, request, user, **kwargs):
    """When a user logs out, see if they sent a request to remove their
    GCM registration_id, as well.

    Since this signal fires AFTER logout, the user is None, and request.user
    is an AnonymousUser object.

    """
    # NOTE: request may be a rest_framework.request.Request object.
    if request.method == "POST" and hasattr(request, "data"):
        registration_id = request.data.get('registration_id', None)
        if registration_id:
            models.GCMDevice.objects.filter(registration_id=registration_id).delete()


class GCMMessageViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    """This endpoint allows an Android client to list a user's scheduled
    notifications (which will be delivered through
    [Google Cloud Messaging](https://developer.android.com/google/gcm)).

    NOTE: the GCM message payload has a limit of 4096 bytes.

    ## Registration

    Devices should be registered at the
    [/api/notifications/devices/](/api/notifications/devices/) endpoint.

    ## Message Details

    You can retrieve the details for an individual message by accessing it's
    unique resource, e.g. `/api/notifications/<id>/`

    ## Updating / Snoozing notifications

    A client may be able to snooze a notification, by sending a PUT request
    to the notifications's detail resource containing the number of hours to
    wait before re-sending the notification.

    For example, send a PUT request to `/api/notifications/42/` with the
    following data in order to re-deliver the message in 24 hours.

        {snooze: 24}


    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GCMMessage.objects.all()
    serializer_class = serializers.GCMMessageSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        """Allow users to snooze their notifications."""
        obj = self.get_object()
        obj.snooze(hours=request.data.pop("snooze", 0))
        ser = self.serializer_class(obj)
        return Response(ser.data)
