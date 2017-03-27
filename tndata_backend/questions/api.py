from django.db.models import Q

from rest_framework import mixins, permissions, status, viewsets

from .serializers import QuestionSerializer, AnswerSerializer
from .models import Question, Answer

class QuestionViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class AnswerViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    

    def get_queryset(self):
        if 'question' in self.request.GET:
            self.queryset = self.queryset.filter(
                question=self.request.GET['question']
            )

        return self.queryset

