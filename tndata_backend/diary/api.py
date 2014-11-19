from rest_framework import serializers, viewsets
from . import models


# Serializers define API representation
class FeelingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Feeling
        fields = ('user', 'rank', 'notes', 'submitted_on')


class FeelingViewSet(viewsets.ModelViewSet):
    queryset = models.Feeling.objects.all()
    serializer_class = FeelingSerializer
