from django.conf.urls import patterns, include, url
from . import views


urlpatterns = patterns('',
    url(
        r'data/$',
        views.RulesDataView.as_view(),
        name='rules-data'
    ),
    url(
        r'^add/$',
        views.AddRuleView.as_view(),
        name='add-rule'
    ),
    url(
        r'(?P<pk>\d+)/$',
        views.RuleDetailView.as_view(),
        name='detail'
    ),
    url(
        r'$',
        views.RulesView.as_view(),
        name='rules'
    ),
)
