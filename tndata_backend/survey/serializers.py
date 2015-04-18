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
    questions = serializers.Field(source='questions')

    class Meta:
        model = Instrument
        fields = ('id', 'title', 'description', 'questions')

    def transform_questions(self, obj, value):
        """Format the list of questions so they can be serialized appropriately."""
        # NOTE: obj is an Instrument instance.
        # value is our list of (class name, question text) tuples.

        # NOTE: This code only works because this is used in a Read-Only
        # endpoint; notice how we pull questions from the Instrument instance,
        # and not the provided value
        if obj and value:
            for i, (qname, question) in enumerate(obj.questions):
                if qname == "BinaryQuestion":
                    value[i] = BinaryQuestionSerializer(question).data
                elif qname == "LikertQuestion":
                    value[i] = LikertQuestionSerializer(question).data
                elif qname == "MultipleChoiceQuestion":
                    value[i] = MultipleChoiceQuestionSerializer(question).data
                elif qname == "OpenEndedQuestion":
                    value[i] = OpenEndedQuestionSerializer(question).data
            return value
        return []


class BinaryQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `BinaryQuestion`."""
    options = BinaryOptionsField()
    question_type = serializers.CharField(source="question_type")
    response_url = serializers.CharField(source="get_api_response_url")

    class Meta:
        model = BinaryQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'options', 'instructions', 'question_type', 'response_url',
        )
        depth = 1


class LikertQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `LikertQuestion`."""
    options = LikertOptionsField()
    question_type = serializers.CharField(source="question_type")
    response_url = serializers.CharField(source="get_api_response_url")

    class Meta:
        model = LikertQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'options', 'instructions', 'question_type', 'response_url',
        )
        depth = 1


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `MultipleChoiceQuestion`."""
    options = MultipleChoiceOptionsField(many=True)
    question_type = serializers.CharField(source="question_type")
    response_url = serializers.CharField(source="get_api_response_url")

    class Meta:
        model = MultipleChoiceQuestion
        fields = (
            'id', 'order', 'text', 'available', 'updated', 'created',
            'options', 'instructions', 'question_type', 'response_url',
        )
        depth = 1


class OpenEndedQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `OpenEndedQuestion`."""
    question_type = serializers.CharField(source="question_type")
    response_url = serializers.CharField(source="get_api_response_url")

    class Meta:
        model = OpenEndedQuestion
        fields = (
            'id', 'order', 'input_type', 'text', 'available', 'updated', 'created',
            'instructions', 'question_type', "response_url",
        )
        depth = 1


# TODO: VALIDATE the response using the question's input_type?
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
