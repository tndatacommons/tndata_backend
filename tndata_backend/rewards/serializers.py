from rest_framework import serializers
from . models import FunContent


class FunContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = FunContent
        fields = (
            'id', 'message_type', 'message', 'author', 'keywords',
        )
