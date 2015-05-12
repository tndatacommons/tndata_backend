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
        # We're creating a single item.
        request.data['user'] = request.user.id
        return super(GCMDeviceViewSet, self).create(request, *args, **kwargs)


class GCMMessageViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """This endpoint allows an Android client to create and schedule a message
    that will be send delivered through
    [Google Cloud Messaging](https://developer.android.com/google/gcm).

    To create a message, you must POST the following information to
    `/api/notifications/`:

    * `registration_id`: This is the device's registration ID. For more info,
      see the [Register for GCM](https://developer.android.com/google/gcm/client.html#sample-register) section in the android developer documentation.
    * `content`: The JSON-encoded message (see more below).
    * `deliver_on`: The date/time on which the message should be delivered, e.g
      `2015-12-24 23:59`.
    * `expire_on`: (optional) A date/time on which this message should be
      expired (deleted from our system).

    ## Content Format

    Notifications delivered to the android app will allow the user to tap on a
    notification, launching the app (possibly with a particular activity).

    The format of the content JSON, should be as follows:

        {
            title: "Notification Title, here",
            message: "Notification Message, here",
            activity: "org.tndatacommons.android.grow.WhateverAvtivity",
            object_id: 42
        }

    The title and message can be arbitrary text, while the activity is the full
    class path name to the activity we want to launch. The object_id is the
    unique identifier for any object that we want to display.

    NOTE: This payload has a limit of 4096 bytes.

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
