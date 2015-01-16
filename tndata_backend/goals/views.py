from django.shortcuts import render
from django.views.generic import DetailView, ListView

from . models import Category


class CategoryList(ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/index.html"


class CategoryDetailView(DetailView):
    queryset = Category.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
