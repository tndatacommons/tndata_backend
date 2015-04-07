from rest_framework import serializers


class BinaryOptionsField(serializers.RelatedField):
    """Includes the available options for a BinaryQuestion. To customize this,
    see `BinaryQuestion.options`."""

    def to_native(self, value):
        # value is a list of options, e.g.:
        # [{'id': False, 'text': 'No'}, {'id': True, 'text': 'Yes'}]
        #
        # We want to convert False -> 0, True -> 1.
        for d in value:
            if d['id'] is False:
                d['id'] = 0
            else:
                d['id'] = 1
        return value


class LikertOptionsField(serializers.RelatedField):
    """Includes the available options for a LIkertQuestion. To customize this,
    see `LikertQuestion.options`."""
    def to_native(self, value):
        # value is a list of options, e.g.:
        # [{'text': 'Strongly Disagree', 'id': 1},
        #  {'text': 'Disagree', 'id': 2},
        #  ...
        #  {'text': 'Strongly Agree', 'id': 5}]
        #
        # We want to ensure that this is always sorted by id.
        return sorted(value, key=lambda d: d['id'])


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
