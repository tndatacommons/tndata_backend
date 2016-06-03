from rest_framework import serializers
from .models import Award, Badge

from utils.serializers import ObjectTypeModelSerializer


class AwardSerializer(ObjectTypeModelSerializer):
    object_type = serializers.SerializerMethodField(read_only=True)
    badge = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Award
        fields = ('id', 'user',  'badge', 'awarded_at', 'object_type')

    def get_badge(self, obj):
        return {
            'id': obj.badge_id,
            'name': obj.badge.name,
            'description': obj.badge.description,
            'image': obj.badge.image.url,
            'users_count': obj.badge.users_count,
        }

    def get_object_type(self, obj):
        return 'award'


class BadgeSerializer(ObjectTypeModelSerializer):
    object_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Badge
        fields = (
            'name', 'slug', 'description', 'image', 'users_count', 'object_type'
        )

    def get_object_type(self, obj):
        return 'badge'
