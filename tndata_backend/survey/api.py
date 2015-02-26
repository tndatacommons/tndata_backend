from rest_framework import viewsets

from . import models
from . import serializers


class LikertQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.LikertQuestion.objects.all()
    serializer_class = serializers.LikertQuestionSerializer


class MultipleChoiceQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.MultipleChoiceQuestion.objects.all()
    serializer_class = serializers.MultipleChoiceQuestionSerializer


class OpenEndedQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.OpenEndedQuestion.objects.all()
    serializer_class = serializers.OpenEndedQuestionSerializer
