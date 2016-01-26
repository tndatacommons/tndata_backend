from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer
from . models import FunContent


class FunContentSerializer(ObjectTypeModelSerializer):

    class Meta:
        model = FunContent
        fields = (
            'id', 'message_type', 'message', 'author', 'keywords',
        )
