from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer
from questions.models import Question


class QuestionSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'title', 'content', 'votes', 'keywords',
                  'created_on', 'updated_on')
