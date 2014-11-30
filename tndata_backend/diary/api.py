from rest_framework import serializers, viewsets
from . import models


# Serializers define API representation
class EntrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Entry
        fields = ('user', 'rank', 'notes', 'submitted_on')


class EntryViewSet(viewsets.ModelViewSet):
    queryset = models.Entry.objects.all()
    serializer_class = EntrySerializer
