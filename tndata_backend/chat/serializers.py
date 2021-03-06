from utils.serializers import ObjectTypeModelSerializer
from rest_framework import serializers
from . models import ChatMessage
from . utils import get_user_details


class ChatMessageSerializer(ObjectTypeModelSerializer):
    # NOTE: This time format really only includes milliseconds. See the
    # `to_representation` comment below.
    created_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S.%f%z")

    class Meta:
        model = ChatMessage
        fields = ('id', 'user', 'room', 'text', 'read', 'digest', 'created_on')

    def to_representation(self, obj):
        """Include the author's username + full name in the message"""
        results = super().to_representation(obj)
        results['user_id'] = str(obj.user.id)
        results['user_username'] = obj.user.username

        name, avatar = get_user_details(obj.user)
        results['user_full_name'] = name
        results['avatar'] = avatar

        # Use Milliseconds instead of Microseconds. We have to split the
        # time zone from the time, then shave off the last 3 digits of the time,
        # then stick them back together.
        ts, tz = results['created_on'].split("+")
        ts = ts[:-3]
        results['created_on'] = "{}+{}".format(ts, tz)

        return results
