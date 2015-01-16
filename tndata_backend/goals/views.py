from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy

from . models import Category


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


class CategoryUpdateView(UpdateView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = ['order', 'name', 'description']


class CategoryDeleteView(DeleteView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')
