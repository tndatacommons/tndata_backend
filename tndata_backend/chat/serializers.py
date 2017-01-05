from utils.serializers import ObjectTypeModelSerializer
from . models import ChatMessage


class ChatMessageSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'user', 'room', 'text', 'read', 'created_on')

    def to_representation(self, obj):
        """Include the author's username + full name in the message"""
        results = super().to_representation(obj)
        results['user_username'] = obj.user.username
        results['user_full_name'] = obj.user.get_full_name()
        return results
