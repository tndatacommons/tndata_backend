from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from . forms import CSVUploadForm
from . models import Action, Category, Interest


def upload_csv(request):
    """Allow a user to upload a CSV file to populate our data backend."""
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # TODO ... process the csv, and save its data.
            data = form.get_data()
            print(data)
            messages.success(request, 'CSV File uploaded, successfully.')
            return redirect("goals:index")
        else:
            messages.warning(request, "This form didn't validate. Please try again.")
    else:
        form = CSVUploadForm()

    context = {'form': form}
    return render(request, 'goals/upload_csv.html', context)


class CategoryListView(ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/index.html"


class CategoryDetailView(DetailView):
    queryset = Category.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class CategoryCreateView(CreateView):
    model = Category
    fields = ['order', 'name', 'description']

    def get_context_data(self, **kwargs):
        context = super(CategoryCreateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryUpdateView(UpdateView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = ['order', 'name', 'description']

    def get_context_data(self, **kwargs):
        context = super(CategoryUpdateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryDeleteView(DeleteView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class InterestListView(ListView):
    model = Interest
    context_object_name = 'interests'


class InterestDetailView(DetailView):
    queryset = Interest.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class InterestCreateView(CreateView):
    model = Interest
    fields = [
        'order', 'name', 'description', 'categories',
        'max_neef_tags', 'sdt_major'
    ]

    def get_context_data(self, **kwargs):
        context = super(InterestCreateView, self).get_context_data(**kwargs)
        context['interests'] = Interest.objects.all()
        return context


class InterestUpdateView(UpdateView):
    model = Interest
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = [
        'order', 'name', 'description', 'categories',
        'max_neef_tags', 'sdt_major'
    ]

    def get_context_data(self, **kwargs):
        context = super(InterestUpdateView, self).get_context_data(**kwargs)
        context['interests'] = Interest.objects.all()
        return context


class InterestDeleteView(DeleteView):
    model = Interest
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class ActionListView(ListView):
    model = Action
    context_object_name = 'actions'


class ActionDetailView(DetailView):
    queryset = Action.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class ActionCreateView(CreateView):
    model = Action
    fields = [
        'order', 'name', 'summary', 'description', 'interests',
        'default_reminder_time', 'default_reminder_frequency',
    ]

    def get_context_data(self, **kwargs):
        context = super(ActionCreateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        return context


class ActionUpdateView(UpdateView):
    model = Action
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = [
        'order', 'name', 'summary', 'description', 'interests',
        'default_reminder_time', 'default_reminder_frequency',
    ]

    def get_context_data(self, **kwargs):
        context = super(ActionUpdateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        return context


class ActionDeleteView(DeleteView):
    model = Action
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')
