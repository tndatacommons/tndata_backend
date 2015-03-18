from rest_framework import serializers
from . models import (
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    OpenEndedQuestion,
)

from . serializer_fields import (
    LikertOptionsField,
    LikertQuestionField,
    MultipleChoiceOptionsField,
)


class LikertQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `LikertQuestion`."""
    options = LikertOptionsField()

    class Meta:
        model = LikertQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created', 'options',
        )


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


class LikertResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `LikertResponse` model."""
    selected_option_text = serializers.Field(source='selected_option_text')
    question = LikertQuestionField(source="question")

    class Meta:
        model = LikertResponse
        fields = (
            'id', 'user', 'question', 'selected_option', 'selected_option_text',
            'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )

    def transform_selected_option(self, obj, value):
        if obj:
            return LikertOptionsField().to_native(obj.selected_option)
        return value
