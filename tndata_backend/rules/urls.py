from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from . import views


urlpatterns = patterns('',
    url(
        r'rules/data/$',
        views.RulesDataView.as_view(),
        name='rules-data'
    ),
    url(
        r'^rules/$',
        TemplateView.as_view(template_name="rules/rules.html"),
        name='rules'
    ),
)
