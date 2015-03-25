from rest_framework import serializers
from . models import (
    BinaryQuestion,
    BinaryResponse,
    Instrument,
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    MultipleChoiceResponse,
    OpenEndedQuestion,
    OpenEndedResponse,
)

from . serializer_fields import (
    BinaryOptionsField,
    LikertOptionsField,
    MultipleChoiceOptionsField,
    QuestionField,
)


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ('id', 'title', 'description')


class BinaryQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `BinaryQuestion`."""
    options = BinaryOptionsField()

    class Meta:
        model = BinaryQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'options', 'instructions', 'instruments'
        )
        depth = 1


class LikertQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `LikertQuestion`."""
    options = LikertOptionsField()

    class Meta:
        model = LikertQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'options', 'instructions', 'instruments'
        )
        depth = 1


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `MultipleChoiceQuestion`."""
    options = MultipleChoiceOptionsField(many=True)

    class Meta:
        model = MultipleChoiceQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'options', 'instructions', 'instruments'
        )
        depth = 1


class OpenEndedQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `OpenEndedQuestion`."""

    class Meta:
        model = OpenEndedQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'instructions', 'instruments'
        )
        depth = 1


class BinaryResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `BinaryResponse` model."""
    selected_option_text = serializers.Field(source='selected_option_text')

    class Meta:
        model = BinaryResponse
        fields = (
            'id', 'user', 'question', 'selected_option', 'selected_option_text',
            'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )

    def transform_selected_option(self, obj, value):
        if obj:
            return BinaryOptionsField().to_native(obj.selected_option)
        return value

    def transform_question(self, obj, value):
        if obj:
            return QuestionField().to_native(obj.question)
        return value


class LikertResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `LikertResponse` model."""
    selected_option_text = serializers.Field(source='selected_option_text')

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

    def transform_question(self, obj, value):
        if obj:
            return QuestionField().to_native(obj.question)
        return value


class MultipleChoiceResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `MultipleChoiceResponse` model."""
    selected_option_text = serializers.Field(source='selected_option_text')

    class Meta:
        model = MultipleChoiceResponse
        fields = (
            'id', 'user', 'question', 'selected_option', 'selected_option_text',
            'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )

    def transform_selected_option(self, obj, value):
        if obj:
            return obj.selected_option.id
        return value

    def transform_question(self, obj, value):
        if obj:
            return QuestionField().to_native(obj.question)
        return value


class OpenEndedResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `OpenEndedResponse` model."""

    class Meta:
        model = OpenEndedResponse
        fields = (
            'id', 'user', 'question', 'response', 'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )

    def transform_question(self, obj, value):
        if obj:
            return QuestionField().to_native(obj.question)
        return value
