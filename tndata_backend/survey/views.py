from collections import Counter

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.db.models import Max
from django.forms.models import modelformset_factory
from django.shortcuts import redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

import pytz
from utils.db import get_max_order

from . forms import (
    BinaryQuestionForm,
    LikertQuestionForm,
    MultipleChoiceQuestionForm,
    OpenEndedQuestionForm,
    SurveyResponseForm,
)
from . models import (
    BinaryQuestion, Instrument, LikertQuestion, MultipleChoiceQuestion,
    MultipleChoiceResponseOption, OpenEndedQuestion, SurveyResult,
)

from . permissions import SurveyAdminsMixin
from clog.clog import clog


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
    form_class = BinaryQuestionForm

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
    form_class = BinaryQuestionForm

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
    form_class = LikertQuestionForm

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
    form_class = LikertQuestionForm

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
    form_class = MultipleChoiceQuestionForm

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
    form_class = MultipleChoiceQuestionForm

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
    form_class = OpenEndedQuestionForm

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
    form_class = OpenEndedQuestionForm

    def get_context_data(self, **kwargs):
        context = super(OpenEndedQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = OpenEndedQuestion.objects.all()
        return context


class OpenEndedQuestionDeleteView(SurveyAdminsMixin, DeleteView):
    model = OpenEndedQuestion
    context_object_name = 'question'
    success_url = reverse_lazy('survey:index')



# Quick & Dirty forms to take a survey.
class TakeSurveyView(SurveyAdminsMixin, ListView):
    """To take the survey, we must first pick an instrument."""
    model = Instrument
    context_object_name = 'instruments'
    template_name = "survey/take_survey.html"


class TakeSurveyQuestionsView(SurveyAdminsMixin, FormView):
    form_class = SurveyResponseForm
    http_method_names = ['get', 'post']
    template_name = "survey/take_survey_questions.html"

    def get_form_kwargs(self):
        kwargs = super(TakeSurveyQuestionsView, self).get_form_kwargs()
        kwargs['instrument'] = self.instrument
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(TakeSurveyQuestionsView, self).get_context_data(**kwargs)
        data['instrument'] = self.instrument
        return data

    def get(self, request, *args, **kwargs):
        self.instrument = Instrument.objects.get(pk=kwargs.get('instrument_id'))
        return super(TakeSurveyQuestionsView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.instrument = Instrument.objects.get(pk=kwargs.get('instrument_id'))
        return super(TakeSurveyQuestionsView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save_responses(self.request.user)
        return super(TakeSurveyQuestionsView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('survey:take-results', args=[self.instrument.id])


class TakeSurveyResultsView(SurveyAdminsMixin, TemplateView):
    template_name = "survey/take_survey_results.html"

    def get(self, request, *args, **kwargs):
        self.user = request.user
        self.instrument = Instrument.objects.get(pk=kwargs.get('instrument_id'))
        return super(TakeSurveyResultsView, self).get(request, *args, **kwargs)

    def _latest_results(self, results):
        """Get the latest set of survey results; results should be a queryset
        of survey results."""
        # Latest set of results via Max truncated date; I *really*, want to do:
        # (select date_trunc('second', max(created_on)) from survey_surveyresult)
        max_date = results.aggregate(Max('created_on'))['created_on__max']

        # Ugh; max_date will be a TZ-aware (in UTC), but our date are stored
        # in the DB with TZ set by settings.TIME_ZONE
        max_date = max_date.astimezone(tz=pytz.timezone(settings.TIME_ZONE))
        return results.filter(
            created_on__year=max_date.year,
            created_on__month=max_date.month,
            created_on__day=max_date.day,
            created_on__hour=max_date.hour,
            created_on__minute=max_date.minute,
            #created_on__second=max_date.second  # TODO: WAT: http://note.io/1QKmSxQ
        )

    def _count_labels(self, qs, n=20):
        """Count the labels based on weighted results from the latest set of
        surveys."""
        # TODO: should move all this into the manager (_latest_results, too)
        c = Counter()
        for r in qs:
            c.update(r.labels * max(r.score, 1))
        return c.most_common(n)

    def get_context_data(self, **kwargs):
        data = super(TakeSurveyResultsView, self).get_context_data(**kwargs)
        data['instrument'] = self.instrument

        # Grab the user's results for this instrument;
        results = SurveyResult.objects.filter(
            user=self.user,
            instrument=self.instrument
        )
        data['results'] = results
        if results.exists():
            latest_results = self._latest_results(results)
            data['latest_results'] = latest_results
            data['labels'] = self._count_labels(latest_results)
        return data
