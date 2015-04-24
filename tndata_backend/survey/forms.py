from django import forms
from django.utils.datastructures import MultiValueDict
from utils.content_labels import LABEL_CHOICES

from . models import (
    BinaryQuestion,
    LikertQuestion,
    MultipleChoiceQuestion,
    OpenEndedQuestion,
)


class ArrayFieldSelectMultiple(forms.SelectMultiple):
    """This is a Form Widget for use with a Postgres ArrayField. It implements
    a multi-select interface that can be given a set of `choices`.

    You can provide a `delimiter` keyword argument to specify the delimeter used.

    """

    def __init__(self, *args, **kwargs):
        self.delimiter = kwargs.pop("delimiter", ",")
        super(ArrayFieldSelectMultiple, self).__init__(*args, **kwargs)

    def render_options(self, choices, value):
        # Value *should* be a list, but it might be a delimited string.
        if isinstance(value, str):
            value = value.split(self.delimiter)
        return super(ArrayFieldSelectMultiple, self).render_options(choices, value)

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            # Normally, we'd want a list here, but the SimpleArrayField
            # expects to get a string
            return self.delimiter.join(data.getlist(name))
        return data.get(name, None)


class BaseQuestionForm(forms.ModelForm):
    """A Base form for all question types. This Form includes the widgets and
    Media definitions for labels (ArrayFields).

    """

    class Meta:
        widgets = {
            "labels": ArrayFieldSelectMultiple(
                choices=LABEL_CHOICES, attrs={'class': 'chosen'}),
        }

    class Media:
        css = {
            "all": ("js/chosen/chosen.min.css", )
        }
        js = ("js/chosen/chosen.jquery.min.js", )


class BinaryQuestionForm(BaseQuestionForm):

    class Meta(BaseQuestionForm.Meta):
        model = BinaryQuestion
        fields = [
            'order', 'subscale', 'text', 'instructions', 'available',
            'labels', 'instruments',
        ]


class LikertQuestionForm(BaseQuestionForm):

    class Meta(BaseQuestionForm.Meta):
        model = LikertQuestion
        fields = [
            'order', 'subscale', 'text', 'instructions', 'available', 'scale',
            'priority', 'labels', 'instruments'
        ]


class MultipleChoiceQuestionForm(BaseQuestionForm):

    class Meta(BaseQuestionForm.Meta):
        model = MultipleChoiceQuestion
        fields = [
            'order', 'subscale', 'text', 'instructions', 'available',
            'labels', 'instruments',
        ]


class OpenEndedQuestionForm(BaseQuestionForm):

    class Meta(BaseQuestionForm.Meta):
        model = OpenEndedQuestion
        fields = [
            'order', 'subscale', 'input_type', 'text', 'instructions',
            'available', 'labels', 'instruments',
        ]
