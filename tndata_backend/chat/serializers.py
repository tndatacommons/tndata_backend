from utils.serializers import ObjectTypeModelSerializer
from . models import ChatMessage


class ChatMessageSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'user', 'room', 'text', 'read', 'created_on')
