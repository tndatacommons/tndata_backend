from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^debug/$',
        views.debug_messages,
        name='debug'
    ),
    url(
        r'(?P<with_user>.*)/$',
        views.chat_view,
        name='chat'
    ),
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),
]
