from datetime import datetime
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.utils import timezone

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

    You may also specify a specific date (including year, month, and day) and
    time (including hour and minute, without timezone information) as a string:

        {time: "14:00", date: "2015-09-01"}

    Examples of acceptable time formats include:

    - 24hr: `9:00`, `09:00`, `13:45`
    - 12hr: `9:00 AM`, `1:45 PM`

    Examples of accepted date formats include:

    - year-month-day: `2015-09-01`
    - month-day-year: `9-1-2015`

    Dates can be specified with or without leading zeros.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GCMMessage.objects.all()
    serializer_class = serializers.GCMMessageSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def _parse_time(self, time):
        dt = None  # The result datetime object
        if time and isinstance(time, list) and len(time) > 0:
            time = time[0]
        if time:
            formats = ["%H:%M", "%I:%M %p", "%I:%M%p"]
            for fmt in formats:
                try:
                    dt = datetime.strptime(time, fmt)
                except ValueError:
                    pass
        return dt

    def _parse_date(self, date):
        dt = None  # The result datetime object
        if date and isinstance(date, list) and len(date) > 0:
            date = date[0]
        if date:
            formats = ["%Y-%m-%d", '%m-%d-%Y']
            for fmt in formats:
                try:
                    dt = datetime.strptime(date, fmt)
                except ValueError:
                    pass
        return dt

    def _combine(self, date=None, time=None):
        dt = None
        if date is None and time is not None:
            # We don't have a date; combine the time with today.
            dt = datetime.now().combine(time)
        elif date is not None and time is not None:
            # We got both: combine them
            dt = datetime.combine(date, time.time())
        return dt

    def update(self, request, *args, **kwargs):
        """Allow users to snooze their notifications."""
        #import ipdb;ipdb.set_trace();

        # Pull the submitted options.
        snooze = request.data.pop("snooze", None)
        time = self._parse_time(request.data.pop("time", None))
        date = self._parse_date(request.data.pop("date", None))
        dt = self._combine(date, time)

        obj = self.get_object()
        if dt:
            obj.snooze(new_datetime=dt)
        elif snooze is not None:
            obj.snooze(hours=snooze)

        ser = self.serializer_class(obj)
        return Response(ser.data)
