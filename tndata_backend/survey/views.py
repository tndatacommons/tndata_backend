from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory

from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from utils.db import get_max_order

from . models import (
    BinaryQuestion, Instrument, LikertQuestion,
    MultipleChoiceQuestion, MultipleChoiceResponseOption, OpenEndedQuestion,
)

from . permissions import SurveyAdminsMixin


class IndexView(SurveyAdminsMixin, TemplateView):
    template_name = "survey/index.html"


class InstrumentListView(SurveyAdminsMixin, ListView):
    model = Instrument
    context_object_name = 'instruments'
    template_name = "survey/instrument_list.html"


class InstrumentDetailView(SurveyAdminsMixin, DetailView):
    queryset = Instrument.objects.all()
    context_object_name = 'instrument'


class InstrumentCreateView(SurveyAdminsMixin, CreateView):
    model = Instrument
    fields = ['title', 'description', 'instructions']

    def get_context_data(self, **kwargs):
        context = super(InstrumentCreateView, self).get_context_data(**kwargs)
        context['instruments'] = Instrument.objects.all()
        return context


class InstrumentUpdateView(SurveyAdminsMixin, UpdateView):
    model = Instrument
    fields = ['title', 'description', 'instructions']

    def get_context_data(self, **kwargs):
        context = super(InstrumentUpdateView, self).get_context_data(**kwargs)
        context['instruments'] = Instrument.objects.all()
        return context


class InstrumentDeleteView(SurveyAdminsMixin, DeleteView):
    model = Instrument
    success_url = reverse_lazy('survey:index')
    context_object_name = 'instrument'


class BinaryQuestionListView(SurveyAdminsMixin, ListView):
    model = BinaryQuestion
    context_object_name = 'questions'
    template_name = "survey/binaryquestion_list.html"


class BinaryQuestionDetailView(SurveyAdminsMixin, DetailView):
    queryset = BinaryQuestion.objects.all()
    context_object_name = 'question'


class BinaryQuestionCreateView(SurveyAdminsMixin, CreateView):
    model = BinaryQuestion
    fields = ['order', 'text', 'instructions', 'available', 'instruments']

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(BinaryQuestionCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(BinaryQuestion)
        return initial

    def get_context_data(self, **kwargs):
        context = super(BinaryQuestionCreateView, self).get_context_data(**kwargs)
        context['questions'] = BinaryQuestion.objects.all()
        context['options'] = BinaryQuestion.OPTIONS
        return context


class BinaryQuestionUpdateView(SurveyAdminsMixin, UpdateView):
    model = BinaryQuestion
    fields = ['order', 'text', 'instructions', 'available', 'instruments']

    def get_context_data(self, **kwargs):
        context = super(BinaryQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = BinaryQuestion.objects.all()
        context['options'] = BinaryQuestion.OPTIONS
        return context


class BinaryQuestionDeleteView(SurveyAdminsMixin, DeleteView):
    model = BinaryQuestion
    success_url = reverse_lazy('survey:index')
    context_object_name = 'question'


class LikertQuestionListView(SurveyAdminsMixin, ListView):
    model = LikertQuestion
    context_object_name = 'questions'
    template_name = "survey/likertquestion_list.html"


class LikertQuestionDetailView(SurveyAdminsMixin, DetailView):
    queryset = LikertQuestion.objects.all()
    context_object_name = 'question'


class LikertQuestionCreateView(SurveyAdminsMixin, CreateView):
    model = LikertQuestion
    fields = [
        'order', 'text', 'instructions', 'available', 'scale',
        'priority', 'instruments'
    ]

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(LikertQuestionCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(LikertQuestion)
        return initial

    def get_context_data(self, **kwargs):
        context = super(LikertQuestionCreateView, self).get_context_data(**kwargs)
        context['questions'] = LikertQuestion.objects.all()
        return context


class LikertQuestionUpdateView(SurveyAdminsMixin, UpdateView):
    model = LikertQuestion
    fields = [
        'order', 'text', 'instructions', 'available', 'scale',
        'priority', 'instruments'
    ]

    def get_context_data(self, **kwargs):
        context = super(LikertQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = LikertQuestion.objects.all()
        return context


class LikertQuestionDeleteView(SurveyAdminsMixin, DeleteView):
    model = LikertQuestion
    success_url = reverse_lazy('survey:index')
    context_object_name = 'question'


class MultipleChoiceQuestionListView(SurveyAdminsMixin, ListView):
    model = MultipleChoiceQuestion
    context_object_name = 'questions'


class MultipleChoiceQuestionDetailView(SurveyAdminsMixin, DetailView):
    queryset = MultipleChoiceQuestion.objects.all()
    context_object_name = 'question'


class MultipleChoiceQuestionCreateView(SurveyAdminsMixin, CreateView):
    model = MultipleChoiceQuestion
    fields = ['order', 'text', 'instructions', 'available', 'instruments']

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(MultipleChoiceQuestionCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(MultipleChoiceQuestion)
        return initial

    def get_formset(self, post_data=None):
        OptionFormSet = modelformset_factory(
            MultipleChoiceResponseOption,
            fields=('text',),
            extra=6
        )
        queryset = MultipleChoiceResponseOption.objects.none()
        if post_data:
            formset = OptionFormSet(post_data, queryset=queryset)
        else:
            formset = OptionFormSet(queryset=queryset)
        return formset

    def get_context_data(self, **kwargs):
        formset = kwargs.pop('formset', self.get_formset())
        context = super(MultipleChoiceQuestionCreateView, self).get_context_data(**kwargs)
        context['questions'] = MultipleChoiceQuestion.objects.all()
        context['formset'] = formset
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.get_formset(request.POST)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        for instance in formset.save(commit=False):
            instance.question = self.object
            instance.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, formset):
        ctx = self.get_context_data(form=form, formset=formset)
        return self.render_to_response(ctx)


class MultipleChoiceQuestionUpdateView(SurveyAdminsMixin, UpdateView):
    model = MultipleChoiceQuestion
    fields = ['order', 'text', 'instructions', 'available', 'instruments']

    def get_formset(self, post_data=None):
        OptionFormSet = modelformset_factory(
            MultipleChoiceResponseOption,
            fields=('text',),
            extra=2
        )
        obj = self.get_object()
        queryset = obj.multiplechoiceresponseoption_set.all()
        if post_data:
            formset = OptionFormSet(post_data, queryset=queryset)
        else:
            formset = OptionFormSet(queryset=queryset)
        return formset

    def get_context_data(self, **kwargs):
        formset = kwargs.pop('formset', self.get_formset())
        context = super(MultipleChoiceQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = MultipleChoiceQuestion.objects.all()
        context['formset'] = formset
        context['object'] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.get_formset(request.POST)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        for instance in formset.save(commit=False):
            instance.question = self.object
            instance.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, formset):
        ctx = self.get_context_data(form=form, formset=formset)
        return self.render_to_response(ctx)


class MultipleChoiceQuestionDeleteView(SurveyAdminsMixin, DeleteView):
    model = MultipleChoiceQuestion
    context_object_name = 'question'
    success_url = reverse_lazy('survey:index')


class OpenEndedQuestionListView(SurveyAdminsMixin, ListView):
    model = OpenEndedQuestion
    context_object_name = 'questions'


class OpenEndedQuestionDetailView(SurveyAdminsMixin, DetailView):
    queryset = OpenEndedQuestion.objects.all()
    context_object_name = 'question'


class OpenEndedQuestionCreateView(SurveyAdminsMixin, CreateView):
    model = OpenEndedQuestion
    fields = ['order', 'input_type', 'text', 'instructions', 'available', 'instruments']

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(OpenEndedQuestionCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(OpenEndedQuestion)
        return initial

    def get_context_data(self, **kwargs):
        context = super(OpenEndedQuestionCreateView, self).get_context_data(**kwargs)
        context['questions'] = OpenEndedQuestion.objects.all()
        return context


class OpenEndedQuestionUpdateView(SurveyAdminsMixin, UpdateView):
    model = OpenEndedQuestion
    fields = ['order', 'input_type', 'text', 'instructions', 'available', 'instruments']

    def get_context_data(self, **kwargs):
        context = super(OpenEndedQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = OpenEndedQuestion.objects.all()
        return context


class OpenEndedQuestionDeleteView(SurveyAdminsMixin, DeleteView):
    model = OpenEndedQuestion
    context_object_name = 'question'
    success_url = reverse_lazy('survey:index')
