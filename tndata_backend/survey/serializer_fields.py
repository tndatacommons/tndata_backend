from rest_framework import serializers


class LikertOptionsField(serializers.RelatedField):
    """Includes the available options for a MultipleChoiceQuestion. To
    customize this, see `MultipleChoiceQuestion.options`."""
    def to_native(self, value):
        return value


class QuestionField(serializers.RelatedField):
    """This is used to serialize a generic Question object. It can be used on
    a related field for LikertQuestions, OpenEndedQuestions, and
    MultipleChoiceQuestions"""
    def to_native(self, value):
        return {
            'id': value.id,
            'text': value.text,
            'created': value.created,
            'updated': value.updated,
        }


class MultipleChoiceOptionsField(serializers.RelatedField):
    """Includes the available options for a MultipleChoiceQuestion. To
    customize this, see `MultipleChoiceQuestion.options`."""
    def to_native(self, value):
        return value
