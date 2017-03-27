from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer
from questions.models import Question, Answer


class QuestionSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'title', 'content', 'votes', 'keywords',
                  'created_on', 'updated_on')


class AnswerSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'user', 'content', 'votes', 'created_on', 'updated_on')

