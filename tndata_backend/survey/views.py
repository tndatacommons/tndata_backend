from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory

from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from utils.db import get_max_order

from . models import (
    Instrument, LikertQuestion, LikertResponse, MultipleChoiceQuestion,
    MultipleChoiceResponseOption, OpenEndedQuestion,
)


def superuser_required(user):
    """Verifies that a user is authenticated and a super user."""
    return user.is_authenticated() and user.is_superuser


class SuperuserRequiredMixin(object):
    """A Mixin that requires the user to be a superuser in order to access
    the view.

    NOTE: Eventually we'll want to have more granular permissions, here. We
    probably need a group or object-level permissions and check for those
    instead (namely, once we have more than just our group editing content)
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(SuperuserRequiredMixin, cls).as_view(**initkwargs)
        dec = user_passes_test(superuser_required, login_url=settings.LOGIN_URL)
        return dec(view)


class IndexView(SuperuserRequiredMixin, TemplateView):
    template_name = "survey/index.html"


class InstrumentListView(SuperuserRequiredMixin, ListView):
    model = Instrument
    context_object_name = 'instruments'
    template_name = "survey/instrument_list.html"


class InstrumentDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Instrument.objects.all()
    context_object_name = 'instrument'


class InstrumentCreateView(SuperuserRequiredMixin, CreateView):
    model = Instrument
    fields = ['title', 'description']

    def get_context_data(self, **kwargs):
        context = super(InstrumentCreateView, self).get_context_data(**kwargs)
        context['instruments'] = Instrument.objects.all()
        return context


class InstrumentUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Instrument
    fields = ['title', 'description']

    def get_context_data(self, **kwargs):
        context = super(InstrumentUpdateView, self).get_context_data(**kwargs)
        context['instruments'] = Instrument.objects.all()
        return context


class InstrumentDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Instrument
    success_url = reverse_lazy('survey:index')
    context_object_name = 'instrument'


class LikertQuestionListView(SuperuserRequiredMixin, ListView):
    model = LikertQuestion
    context_object_name = 'questions'
    template_name = "survey/likertquestion_list.html"


class LikertQuestionDetailView(SuperuserRequiredMixin, DetailView):
    queryset = LikertQuestion.objects.all()
    context_object_name = 'question'


class LikertQuestionCreateView(SuperuserRequiredMixin, CreateView):
    model = LikertQuestion
    fields = ['order', 'text', 'available', 'instruments']

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
        context['options'] = LikertQuestion.LIKERT_CHOICES
        return context


class LikertQuestionUpdateView(SuperuserRequiredMixin, UpdateView):
    model = LikertQuestion
    fields = ['order', 'text', 'available', 'instruments']

    def get_context_data(self, **kwargs):
        context = super(LikertQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = LikertQuestion.objects.all()
        context['options'] = LikertQuestion.LIKERT_CHOICES
        return context


class LikertQuestionDeleteView(SuperuserRequiredMixin, DeleteView):
    model = LikertQuestion
    success_url = reverse_lazy('survey:index')
    context_object_name = 'question'


class MultipleChoiceQuestionListView(SuperuserRequiredMixin, ListView):
    model = MultipleChoiceQuestion
    context_object_name = 'questions'


class MultipleChoiceQuestionDetailView(SuperuserRequiredMixin, DetailView):
    queryset = MultipleChoiceQuestion.objects.all()
    context_object_name = 'question'


class MultipleChoiceQuestionCreateView(SuperuserRequiredMixin, CreateView):
    model = MultipleChoiceQuestion
    fields = ['order', 'text', 'available', 'instruments']

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


class MultipleChoiceQuestionUpdateView(SuperuserRequiredMixin, UpdateView):
    model = MultipleChoiceQuestion
    fields = ['order', 'text', 'available', 'instruments']

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


class MultipleChoiceQuestionDeleteView(SuperuserRequiredMixin, DeleteView):
    model = MultipleChoiceQuestion
    context_object_name = 'question'
    success_url = reverse_lazy('survey:index')


class OpenEndedQuestionListView(SuperuserRequiredMixin, ListView):
    model = OpenEndedQuestion
    context_object_name = 'questions'


class OpenEndedQuestionDetailView(SuperuserRequiredMixin, DetailView):
    queryset = OpenEndedQuestion.objects.all()
    context_object_name = 'question'


class OpenEndedQuestionCreateView(SuperuserRequiredMixin, CreateView):
    model = OpenEndedQuestion
    fields = ['order', 'text', 'available', 'instruments']

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


class OpenEndedQuestionUpdateView(SuperuserRequiredMixin, UpdateView):
    model = OpenEndedQuestion
    fields = ['order', 'text', 'available', 'instruments']

    def get_context_data(self, **kwargs):
        context = super(OpenEndedQuestionUpdateView, self).get_context_data(**kwargs)
        context['questions'] = OpenEndedQuestion.objects.all()
        return context


class OpenEndedQuestionDeleteView(SuperuserRequiredMixin, DeleteView):
    model = OpenEndedQuestion
    context_object_name = 'question'
    success_url = reverse_lazy('survey:index')
