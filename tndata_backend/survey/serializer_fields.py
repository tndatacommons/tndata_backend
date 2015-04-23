from rest_framework import serializers
from .models import MultipleChoiceResponseOption


def _get_object(model, pk):
    """Given a data model class and a primary key value, try to look up an
    object; If the object is not found, raise a ValidationError."""
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        msg = 'Could not find a {0} instance with a key of {1}'
        raise serializers.ValidationError(msg.format(model.__name__, pk))


class BinaryOptionsField(serializers.RelatedField):
    """Includes the available options for a BinaryQuestion. To customize this,
    see `BinaryQuestion.options`."""

    def to_representation(self, value):
        # value is a list of options, e.g.:
        # [{'id': False, 'text': 'No'}, {'id': True, 'text': 'Yes'}]
        #
        # We want to convert False -> 0, True -> 1.
        if isinstance(value, list):
            for d in value:
                if d['id'] is False:
                    d['id'] = 0
                else:
                    d['id'] = 1
        return value


class LikertOptionsField(serializers.RelatedField):
    """Includes the available options for a LIkertQuestion. To customize this,
    see `LikertQuestion.options`."""

    def to_internal_value(self, data):
        # Likert options are not model instances, so this is a bit of a hack.
        return data

    def to_representation(self, value):
        # value is a list of options, e.g.:
        # [{'text': 'Strongly Disagree', 'id': 1},
        #  {'text': 'Disagree', 'id': 2},
        #  ...
        #  {'text': 'Strongly Agree', 'id': 5}]
        #
        # We want to ensure that this is always sorted by id.
        if isinstance(value, list):
            return sorted(value, key=lambda d: d['id'])
        return value


class QuestionField(serializers.RelatedField):
    """This is used to serialize a generic Question object. It can be used on
    a related field for LikertQuestions, OpenEndedQuestions, and
    MultipleChoiceQuestions"""

    def to_internal_value(self, data):
        # data could be an int or a dict?
        if isinstance(data, int):
            return _get_object(self.queryset.model, data)
        return _get_object(self.queryset.model, data.get('id'))

    def to_representation(self, value):
        return {
            'id': value.id,
            'text': value.text,
            'created': value.created,
            'updated': value.updated,
        }


class MultipleChoiceResponseOptionField(serializers.RelatedField):
    """Includes the available options for a MultipleChoiceQuestion. To
    customize this, see `MultipleChoiceQuestion.options`."""

    def to_internal_value(self, data):
        # data is a dict of POSTed info
        if isinstance(data, int):
            return _get_object(MultipleChoiceResponseOption, data)
        return _get_object(MultipleChoiceResponseOption, data.get('id'))

    def to_representation(self, value):
        # value is a MultipleChoiceResponseOption instance or a dict
        # WANT: {'text': 'Male', 'id': 1}
        if isinstance(value, dict):
            return value
        return {'text': value.text, 'id': value.id}
