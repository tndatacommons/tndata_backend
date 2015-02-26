from rest_framework import serializers
from . models import (
    LikertQuestion,
    MultipleChoiceQuestion,
    OpenEndedQuestion,
)


class LikertOptionsField(serializers.RelatedField):
    """Includes the available options for a MultipleChoiceQuestion. To
    customize this, see `MultipleChoiceQuestion.options`."""
    def to_native(self, value):
        return value


class LikertQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `LikertQuestion`."""
    options = LikertOptionsField()

    class Meta:
        model = LikertQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created', 'options',
        )


class MultipleChoiceOptionsField(serializers.RelatedField):
    """Includes the available options for a MultipleChoiceQuestion. To
    customize this, see `MultipleChoiceQuestion.options`."""
    def to_native(self, value):
        return value


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `MultipleChoiceQuestion`."""
    options = MultipleChoiceOptionsField(many=True)

    class Meta:
        model = MultipleChoiceQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created', 'options',
        )


class OpenEndedQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `MultipleChoiceQuestion`."""

    class Meta:
        model = OpenEndedQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
        )
