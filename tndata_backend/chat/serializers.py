from utils.serializers import ObjectTypeModelSerializer
from rest_framework import serializers
from . models import ChatMessage


class ChatMessageSerializer(ObjectTypeModelSerializer):
    created_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S.%f%z")

    class Meta:
        model = ChatMessage
        fields = ('id', 'user', 'room', 'text', 'read', 'digest', 'created_on')

    def to_representation(self, obj):
        """Include the author's username + full name in the message"""
        results = super().to_representation(obj)
        results['user_id'] = str(obj.user.id)
        results['user_username'] = obj.user.username
        results['user_full_name'] = obj.user.get_full_name()
        return results
