from datetime import datetime
from django.contrib.auth.signals import user_logged_out
from django.db.models import Q
from django.dispatch import receiver

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)
from rest_framework.response import Response
from utils.user_utils import hash_value

from . import models
from . import serializers


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class GCMDeviceViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    """This endpoint allows an Android client to register a User's device for
    notifications via
    [Google Cloud Messaging](https://developer.android.com/google/gcm).

    To register a device, you must POST the following information to
    `/api/notifications/devices/`:

    * `registration_id`: This is the device's registration ID. For more info,
      see the [Register for GCM](https://developer.android.com/google/gcm/client.html#sample-register) section in the android developer documentation.
    * `device_type`: should be `android` or `ios`.
    * `device_name`: (optional) a name for the device. It's best to provide
      this information if possible.

    GET requests to this enpoint will list a user's registered devices, including
    the following information:

    * `id`: A unique Database ID for the device.
    * `user`: The device owner's database ID
    * `device_name`: The supplied name for the device
    * `device_id`: A unique identifier for the device. This is used along with
      the user's information to uniquely identify a device, and to update the
      registration id when it changes.
    * `registration_id`: This is the device's registration ID. For more info,
      see the [Register for GCM](https://developer.android.com/google/gcm/client.html#sample-register) section in the android developer documentation.
    * `created_on`: The date the device data was created
    * `updated_on`: The date the device data was last updated
    * `object_type`: Will always be the string "gcmdevice"

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GCMDevice.objects.all()
    serializer_class = serializers.GCMDeviceSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def _update(self, request, device_id=None):
        """Update the user's registration ID for the given device_id. If not
        device ID is given, or if the device ID is not found, this method will
        update any of the user's GCMDevice entries, and remove those without
        a device id.

        """
        device = None
        device_name = request.data.get('device_name', '')
        device_type = request.data.get('device_type', 'android')
        registration_id = request.data.get('registration_id', None)

        try:
            # Device ID is given, try updating that.
            params = {'user': request.user, 'device_id': device_id}
            device = models.GCMDevice.objects.get(**params)
        except (models.GCMDevice.DoesNotExist, models.GCMDevice.MultipleObjectsReturned):
            # Device ID doesn't exist in our DB, just pick a device who's
            # ID is None and update it.
            params = {'user': request.user, 'device_id': None}
            device = models.GCMDevice.objects.filter(**params).first()

        if device:
            device.device_id = device_id
            device.device_name = device_name
            device.registration_id = registration_id
            device.device_type = device_type
            device.save()

        if device and device_id:
            # If we _did_ update the device with an ID, remove all of the old
            # None-type device objects.
            params = {'user': request.user, 'device_id': None}
            models.GCMDevice.objects.filter(**params).delete()

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(device)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Handles POST requests, but this method also checks for existing
        instances of a device, and calls `update` when appropriate."""

        # Only do this for authenticated users.
        if request.user.is_authenticated():
            request.data['user'] = request.user.id

            # Generate the device id (a hash of device name + user email)
            device_name = request.data.get('device_name', 'unkown')
            device_id = hash_value("{}+{}".format(request.user.email, device_name))
            request.data['device_id'] = device_id

            # If device_type isn't specified, default to 'android'
            if not request.data.get('device_type', None):
                request.data['device_type'] = 'android'

            # Check to see if the Registration ID already exists:
            reg_id = request.data.get('registration_id', None)
            params = {'user': request.user, 'registration_id': reg_id}
            if reg_id and models.GCMDevice.objects.filter(**params).exists():
                return Response(None, status=status.HTTP_304_NOT_MODIFIED)

            # Otherwise, look for this device, and update its registration id
            devices = models.GCMDevice.objects.filter(user=request.user).filter(
                Q(device_id=device_id) | Q(device_id=None)
            )
            if devices.exists():
                return self._update(request, device_id=device_id)

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

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj)
        return Response(serializer.data)
