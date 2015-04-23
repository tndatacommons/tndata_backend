from rest_framework import serializers
from . models import (
    BinaryQuestion,
    BinaryResponse,
    Instrument,
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    MultipleChoiceResponse,
    MultipleChoiceResponseOption,
    OpenEndedQuestion,
    OpenEndedResponse,
)

from . serializer_fields import (
    BinaryOptionsField,
    LikertOptionsField,
    MultipleChoiceResponseOptionField,
    QuestionField,
)


class InstrumentSerializer(serializers.ModelSerializer):
    questions = serializers.ReadOnlyField()

    class Meta:
        model = Instrument
        fields = ('id', 'title', 'description', 'instructions', 'questions')

    def to_representation(self, instance):
        """Format the list of questions so they can be serialized appropriately."""
        # NOTE: obj is an Instrument instance.
        # value is our list of (class name, question text) tuples.

        # NOTE: This code only works because this is used in a Read-Only
        # endpoint; notice how we pull questions from the Instrument instance,
        # and not the provided value
        ret = super(InstrumentSerializer, self).to_representation(instance)
        questions = []
        for i, (qname, question) in enumerate(instance.questions):
            if qname == "BinaryQuestion":
                questions.append(BinaryQuestionSerializer(question).data)
            elif qname == "LikertQuestion":
                questions.append(LikertQuestionSerializer(question).data)
            elif qname == "MultipleChoiceQuestion":
                questions.append(MultipleChoiceQuestionSerializer(question).data)
            elif qname == "OpenEndedQuestion":
                questions.append(OpenEndedQuestionSerializer(question).data)
        ret['questions'] = questions
        return ret


class BinaryQuestionSerializer(serializers.ModelSerializer):
    """A Serializer for `BinaryQuestion`."""
    options = BinaryOptionsField(read_only=True)
    question_type = serializers.CharField()
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
    options = LikertOptionsField(read_only=True)
    question_type = serializers.CharField()
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
    options = MultipleChoiceResponseOptionField(many=True, read_only=True)
    question_type = serializers.CharField()
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
    question_type = serializers.CharField()
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
    selected_option_text = serializers.ReadOnlyField()
    selected_option = BinaryOptionsField(read_only=True)
    question = QuestionField(queryset=BinaryQuestion.objects.all())

    class Meta:
        model = BinaryResponse
        fields = (
            'id', 'user', 'question', 'selected_option', 'selected_option_text',
            'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )


class LikertResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `LikertResponse` model."""
    selected_option_text = serializers.ReadOnlyField()
    # This isn't really a RelatedField, but I'm not sure how to do this, other
    # wise, so this is a bit of a hack; we need to placate the need for a
    # queryset, even those this makes no sense.
    selected_option = LikertOptionsField(
        queryset=LikertQuestion.objects.none()
    )
    question = QuestionField(queryset=LikertQuestion.objects.all())

    class Meta:
        model = LikertResponse
        fields = (
            'id', 'user', 'question', 'selected_option', 'selected_option_text',
            'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )


class MultipleChoiceResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `MultipleChoiceResponse` model."""
    selected_option_text = serializers.ReadOnlyField()
    selected_option = MultipleChoiceResponseOptionField(
        queryset=MultipleChoiceResponseOption.objects.all()
    )
    question = QuestionField(queryset=MultipleChoiceQuestion.objects.all())

    class Meta:
        model = MultipleChoiceResponse
        fields = (
            'id', 'user', 'question', 'selected_option', 'selected_option_text',
            'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )


class OpenEndedResponseSerializer(serializers.ModelSerializer):
    """A Serializer for the `OpenEndedResponse` model."""
    question = QuestionField(queryset=OpenEndedQuestion.objects.all())

    class Meta:
        model = OpenEndedResponse
        fields = (
            'id', 'user', 'question', 'response', 'submitted_on'
        )
        read_only_fields = ("id", "submitted_on", )

    def validate(self, attrs):
        try:
            # Try to convert the given response into the question's input_type;
            # if this fails, it will raise an Exception
            attrs['question'].convert_to_input_type(attrs['response'])
        except ValueError:
            raise serializers.ValidationError("The response is not a valid input_type")
        return attrs
