from rest_framework import serializers
from . models import GCMDevice, GCMMessage


class GCMDeviceSerializer(serializers.ModelSerializer):
    """A Serializer for the `GCMDevice` model."""

    class Meta:
        model = GCMDevice
        fields = (
            'id', 'user', 'registration_id', 'device_name', 'is_active',
            'created_on', 'updated_on',
        )
        read_only_fields = ("id", "created_on", "updated_on")


class GCMMessageSerializer(serializers.ModelSerializer):
    """A Serializer for the `GCMMessage` model."""

    class Meta:
        model = GCMMessage
        fields = (
            'id', 'user', 'message_id', 'content',
            'success', 'response_code', 'response_text', 'deliver_on',
            'expire_on', 'created_on',
        )
        read_only_fields = (
            "id", "success", "response_code", "response_text", "created_on",
        )

    def to_representation(self, instance):
        """Return a JSON-decoded version of the content, because rest framework
        will re-encode it."""
        ret = super(GCMMessageSerializer, self).to_representation(instance)
        ret['content'] = instance.content
        return ret
