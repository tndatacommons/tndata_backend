from rest_framework import viewsets

from . import models
from . import serializers


class FunContentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.FunContent.objects.all()
    serializer_class = serializers.FunContentSerializer
