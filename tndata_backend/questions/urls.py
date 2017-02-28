from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^(?P<pk>\d+)/(?P<title_slug>.*)/answer/(?P<answer_pk>\d+)/upvote/$',
        views.upvote_answer,
        name='upvote-answer'
    ),
    url(
        r'^(?P<pk>\d+)/(?P<title_slug>.*)/answer/$',
        views.post_answer,
        name='post-answer'
    ),
    url(
        r'^(?P<pk>\d+)/(?P<title_slug>.*)/upvote/$',
        views.upvote_question,
        name='upvote-question'
    ),
    url(
        r'^(?P<pk>\d+)/(?P<title_slug>.*)/$',
        views.question_details,
        name='question-details'
    ),
    url(r'^ask/$', views.ask_question, name='ask'),
    url(r'^ask/(?P<title>.*)/$', views.ask_question, name='ask_with_title'),
    url(r'^$', views.index, name='index'),  # list of questions + form to ask
]
