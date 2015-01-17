from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy

from . models import Action, Category, Interest


class CategoryList(ListView):
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
