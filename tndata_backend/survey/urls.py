from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),

    # Create views
    url(
        r'new/instrument/$',
        views.InstrumentCreateView.as_view(),
        name='instrument-create'
    ),
    url(
        r'new/binary/$',
        views.BinaryQuestionCreateView.as_view(),
        name='binary-create'
    ),
    url(
        r'new/likert/$',
        views.LikertQuestionCreateView.as_view(),
        name='likert-create'
    ),
    url(
        r'new/multiplechoice/$',
        views.MultipleChoiceQuestionCreateView.as_view(),
        name='multiplechoice-create'
    ),
    url(
        r'new/openended/$',
        views.OpenEndedQuestionCreateView.as_view(),
        name='openended-create'
    ),

    # Instruments
    url(
        r'instrument/$',
        views.InstrumentListView.as_view(),
        name='instrument-list'
    ),
    url(
        r'instrument/(?P<pk>\d+)/update/$',
        views.InstrumentUpdateView.as_view(),
        name='instrument-update'
    ),
    url(
        r'instrument/(?P<pk>\d+)/delete/$',
        views.InstrumentDeleteView.as_view(),
        name='instrument-delete'
    ),
    url(
        r'instrument/(?P<pk>\d+)/$',
        views.InstrumentDetailView.as_view(),
        name='instrument-detail'
    ),

    # BinaryQuestions
    url(
        r'binary/$',
        views.BinaryQuestionListView.as_view(),
        name='binary-list'
    ),
    url(
        r'binary/(?P<pk>\d+)/update/$',
        views.BinaryQuestionUpdateView.as_view(),
        name='binary-update'
    ),
    url(
        r'binary/(?P<pk>\d+)/delete/$',
        views.BinaryQuestionDeleteView.as_view(),
        name='binary-delete'
    ),
    url(
        r'binary/(?P<pk>\d+)/$',
        views.BinaryQuestionDetailView.as_view(),
        name='binary-detail'
    ),

    # LikertQuestions
    url(
        r'likert/$',
        views.LikertQuestionListView.as_view(),
        name='likert-list'
    ),
    url(
        r'likert/(?P<pk>\d+)/update/$',
        views.LikertQuestionUpdateView.as_view(),
        name='likert-update'
    ),
    url(
        r'likert/(?P<pk>\d+)/delete/$',
        views.LikertQuestionDeleteView.as_view(),
        name='likert-delete'
    ),
    url(
        r'likert/(?P<pk>\d+)/$',
        views.LikertQuestionDetailView.as_view(),
        name='likert-detail'
    ),

    # MultipleChoiceQuestions
    url(
        r'multiplechoice/$',
        views.MultipleChoiceQuestionListView.as_view(),
        name='multiplechoice-list'
    ),
    url(
        r'multiplechoice/(?P<pk>\d+)/update/$',
        views.MultipleChoiceQuestionUpdateView.as_view(),
        name='multiplechoice-update'
    ),
    url(
        r'multiplechoice/(?P<pk>\d+)/delete/$',
        views.MultipleChoiceQuestionDeleteView.as_view(),
        name='multiplechoice-delete'
    ),
    url(
        r'multiplechoice/(?P<pk>\d+)/$',
        views.MultipleChoiceQuestionDetailView.as_view(),
        name='multiplechoice-detail'
    ),

    # OpenEndedQuestions
    url(
        r'openended/$',
        views.OpenEndedQuestionListView.as_view(),
        name='openended-list'
    ),
    url(
        r'openended/(?P<pk>\d+)/update/$',
        views.OpenEndedQuestionUpdateView.as_view(),
        name='openended-update'
    ),
    url(
        r'openended/(?P<pk>\d+)/delete/$',
        views.OpenEndedQuestionDeleteView.as_view(),
        name='openended-delete'
    ),
    url(
        r'openended/(?P<pk>\d+)/$',
        views.OpenEndedQuestionDetailView.as_view(),
        name='openended-detail'
    ),

)
