from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from . forms import CSVUploadForm, TriggerForm
from . models import (
    Action, Behavior, Category, Goal, Trigger
)
from utils.db import get_max_order


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


@user_passes_test(superuser_required, login_url='/')
def upload_csv(request):
    """Allow a user to upload a CSV file to populate our data backend."""
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'CSV File uploaded, successfully.')
                return redirect("goals:index")
            except CSVUploadForm.InvalidFormat as e:
                messages.error(
                    request, "The uploaded file could not be "
                    "processed. Please check the format and try again: "
                    " {0}".format(e)
                )
        else:
            messages.warning(
                request, "This form didn't validate. Please try again."
            )
    else:
        form = CSVUploadForm()

    context = {'form': form}
    return render(request, 'goals/upload_csv.html', context)


class IndexView(SuperuserRequiredMixin, TemplateView):
    template_name = "goals/index.html"


class CategoryListView(SuperuserRequiredMixin, ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/category_list.html"


class CategoryDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Category.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class CategoryCreateView(SuperuserRequiredMixin, CreateView):
    model = Category
    fields = ['order', 'title', 'description', 'icon', 'notes']

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(CategoryCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(Category)
        return initial

    def get_context_data(self, **kwargs):
        context = super(CategoryCreateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Category
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    fields = ['order', 'title', 'description', 'icon', 'notes']

    def get_context_data(self, **kwargs):
        context = super(CategoryUpdateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Category
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


class GoalListView(SuperuserRequiredMixin, ListView):
    model = Goal
    context_object_name = 'goals'


class GoalDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Goal.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class GoalCreateView(SuperuserRequiredMixin, CreateView):
    model = Goal
    fields = [
        'categories', 'title', 'subtitle', 'description', 'outcome', 'icon',
    ]

    def get_context_data(self, **kwargs):
        context = super(GoalCreateView, self).get_context_data(**kwargs)
        context['goals'] = Goal.objects.all()
        return context


class GoalUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Goal
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    fields = [
        'categories', 'title', 'subtitle', 'description', 'outcome', 'icon',
    ]

    def get_context_data(self, **kwargs):
        context = super(GoalUpdateView, self).get_context_data(**kwargs)
        context['goals'] = Goal.objects.all()
        return context


class GoalDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Goal
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


class TriggerListView(SuperuserRequiredMixin, ListView):
    model = Trigger
    context_object_name = 'triggers'


class TriggerDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Trigger.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class TriggerCreateView(SuperuserRequiredMixin, CreateView):
    model = Trigger
    form_class = TriggerForm

    def get_context_data(self, **kwargs):
        context = super(TriggerCreateView, self).get_context_data(**kwargs)
        context['triggers'] = Trigger.objects.all()
        return context


class TriggerUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Trigger
    form_class = TriggerForm
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def get_context_data(self, **kwargs):
        context = super(TriggerUpdateView, self).get_context_data(**kwargs)
        context['triggers'] = Trigger.objects.all()
        return context


class TriggerDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Trigger
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class BehaviorListView(SuperuserRequiredMixin, ListView):
    model = Behavior
    context_object_name = 'behaviors'


class BehaviorDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Behavior.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class BehaviorCreateView(SuperuserRequiredMixin, CreateView):
    model = Behavior
    fields = [
        'title', 'source_link', 'source_notes', 'notes', 'narrative_block',
        'description', 'outcome', 'external_resource', 'informal_list',
        'categories', 'goals', 'icon', 'image',
    ]

    def get_context_data(self, **kwargs):
        context = super(BehaviorCreateView, self).get_context_data(**kwargs)
        context['behaviors'] = Behavior.objects.all()
        return context


class BehaviorUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Behavior
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    fields = [
        'title', 'source_link', 'source_notes', 'notes', 'narrative_block',
        'description', 'outcome', 'external_resource', 'informal_list',
        'categories', 'goals', 'icon', 'image',
    ]

    def get_context_data(self, **kwargs):
        context = super(BehaviorUpdateView, self).get_context_data(**kwargs)
        context['behaviors'] = Behavior.objects.all()
        return context


class BehaviorDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Behavior
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


class ActionListView(SuperuserRequiredMixin, ListView):
    model = Action
    context_object_name = 'actions'


class ActionDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Action.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class ActionCreateView(SuperuserRequiredMixin, CreateView):
    model = Action
    fields = [
        'sequence_order','sequence', 'title', 'source_link', 'source_notes',
        'notes', 'narrative_block', 'description', 'outcome', 'default_trigger',
        'notification_text', 'icon', 'image',
    ]

    def get_context_data(self, **kwargs):
        context = super(ActionCreateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        context['behaviors'] = Behavior.objects.all()
        return context


class ActionUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Action
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    fields = [
        'sequence_order','sequence', 'title', 'source_link', 'source_notes',
        'notes', 'narrative_block', 'description', 'outcome', 'default_trigger',
        'notification_text', 'icon', 'image',
    ]

    def get_context_data(self, **kwargs):
        context = super(ActionUpdateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        context['behaviors'] = Behavior.objects.all()
        return context


class ActionDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Action
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')
