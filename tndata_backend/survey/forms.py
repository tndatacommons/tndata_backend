from django import forms
from django.utils.datastructures import MultiValueDict

from . labels import get_label_choices
from . models import (
    BinaryQuestion,
    BinaryResponse,
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    MultipleChoiceResponse,
    OpenEndedQuestion,
    OpenEndedResponse,
    SurveyResult
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
                choices=get_label_choices(), attrs={'class': 'chosen'}),
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



class SurveyResponseForm(forms.Form):
    """EXPERIMENTAL! This is a dynamically generated form containing all
    questions/options for a given instrument.

    """

    def __init__(self, *args, **kwargs):
        self._models = {}
        self.instrument = kwargs.pop("instrument")
        if self.instrument is None:
            raise TypeError("SurveyResponseForm requires an instrument argument")

        super(SurveyResponseForm, self).__init__(*args, **kwargs)
        self._build_fields()
        # Keep a dict of the question field id that maps to the question model
        # and response model so we can create responses.

    def _build_fields(self):
        # Iterate over the instrument's questions and create appropriate fields.
        self.fields = {}
        accepted_question_types = {
            "LikertQuestion", 'BinaryQuestion',
            'MultipleChoiceQuestion', 'OpenEndedQuestion'
        }
        question_types = set(t for t, q in self.instrument.questions)
        if question_types.issubset(accepted_question_types):
            msg = "Only Instruments with Likert and Binary Questions are supported"
            self.cleaned_data = {}  # hack so add_error doesn't fail
            self.add_error(None, msg)
            #raise forms.ValidationError(msg, code="invalid")

        for qtype, question in self.instrument.questions:
            question_key = "question_{0}".format(question.id)
            if qtype == "LikertQuestion":
                self._models[question_key] = {
                    'question': question,
                    'response_model': LikertResponse,
                    'response_field': 'selected_option',
                }
                self.fields[question_key] = forms.ChoiceField(
                    label=question.text,
                    choices=((o['id'], o['text']) for o in question.options),
                    help_text=question.instructions
                )
            elif qtype == "BinaryQuestion":
                self._models[question_key] = {
                    'question': question,
                    'response_model': BinaryResponse,
                    'response_field': 'selected_option',
                }
                self.fields[question_key] = forms.ChoiceField(
                    label=question.text,
                    choices=((o['id'], o['text']) for o in question.options),
                    help_text=question.instructions
                )
            elif qtype == "MultipleChoiceQuestion":
                self._models[question_key] = {
                    'question': question,
                    'response_model': MultipleChoiceResponse,
                    'response_field': 'selected_option',
                }
                self.fields[question_key] = forms.ChoiceField(
                    label=question.text,
                    choices=((o['id'], o['text']) for o in question.options),
                    help_text=question.instructions
                )
            elif qtype == "OpenEndedQuestion":
                self._models[question_key] = {
                    'question': question,
                    'response_model': OpenEndedResponse,
                    'response_field': 'response',
                }
                self.fields[question_key] = forms.CharField(
                    label=question.text,
                    help_text=question.instructions
                )

    def save_responses(self, user):
        # Once validation has passes, create responses for the form's
        # questions, then generate a SurveyResponse object?
        #
        # cleaned_data will look like this:
        #
        # {'question_1': 'False',
        #  'question_2': 'asdf',
        #  'question_28': '1',
        #  'question_8': '47'}
        for question_id, value in self.cleaned_data.items():
            # Create a survey response
            question = self._models[question_id]['question']
            response_field = self._models[question_id]['response_field']
            Model = self._models[question_id]['response_model']
            kwargs = {
                'user': user,
                'question': question,
                response_field: self.cleaned_data[question_id],
            }
            Model.objects.create(**kwargs)

        # create SurveyResult object(s)
        return SurveyResult.objects.create_objects(user, self.instrument)
