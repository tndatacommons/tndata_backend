from django.shortcuts import render
from django.views.generic import ListView
from . models import Category


class CategoryList(ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/index.html"
