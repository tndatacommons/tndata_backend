from django.db.models import Q

from rest_framework import mixins, permissions, status, viewsets

from .serializers import QuestionSerializer
from .models import Question

class QuestionViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

