from rest_framework import serializers
from .models import Award, Badge

from utils.serializers import ObjectTypeModelSerializer


class BadgeSerializer(ObjectTypeModelSerializer):
    object_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Badge
        fields = (
            'name', 'slug', 'description', 'image', 'users_count', 'object_type'
        )

    def get_object_type(self, obj):
        return 'badge'


class AwardSerializer(ObjectTypeModelSerializer):
    object_type = serializers.SerializerMethodField(read_only=True)
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = Award
        fields = ('id', 'user',  'badge', 'awarded_at', 'object_type')

    def get_object_type(self, obj):
        return 'award'
