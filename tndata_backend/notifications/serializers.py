from rest_framework import serializers
from . models import GCMMessage


class GCMMessageSerializer(serializers.ModelSerializer):
    """A Serializer for the `GCMMessage` model."""

    class Meta:
        model = GCMMessage
        fields = (
            'id', 'user', 'message_id', 'registration_id', 'content',
            'success', 'response_code', 'response_text', 'deliver_on',
            'expire_on', 'created_on',
        )
        read_only_fields = (
            "id", "message_id", "success", "response_code",
            "response_text", "created_on",
        )

    def transform_content(self, obj, value):
        """Return a JSON-decoded version of the content, because rest framework
        will re-encode it."""
        if obj and isinstance(obj, GCMMessage):
            return obj.get_content_data()
        elif obj:
            return obj
        return value
