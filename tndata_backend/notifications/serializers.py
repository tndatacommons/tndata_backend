from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer
from . models import GCMDevice, GCMMessage


class GCMDeviceSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `GCMDevice` model."""

    class Meta:
        model = GCMDevice
        fields = (
            'id', 'user','device_name', 'device_id', 'registration_id',
            'is_active', 'created_on', 'updated_on', 'oject_type',
        )
        read_only_fields = ("id", "created_on", "updated_on")


class GCMMessageSerializer(ObjectTypeModelSerializer):
    """A Serializer for the `GCMMessage` model."""

    class Meta:
        model = GCMMessage
        fields = (
            'id', 'user', 'content', 'success', 'response_code',
            'deliver_on', 'created_on', 'object_type',
        )
