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

    def to_representation(self, instance):
        """Return a JSON-decoded version of the content, because rest framework
        will re-encode it."""
        ret = super(GCMMessageSerializer, self).to_representation(instance)
        ret['content'] = instance.get_content_data()
        return ret
