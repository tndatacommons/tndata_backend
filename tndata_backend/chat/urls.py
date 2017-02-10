from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^debug/$',
        views.debug_messages,
        name='debug'
    ),
    url(
        r'^contacts/$',
        views.contacts,
        name='contacts'
    ),
    url(
        r'group/(?P<pk>\d+)-(?P<slug>.*)/$',
        views.group_chat_view,
        name='group-chat'
    ),
    url(
        r'(?P<recipient_id>\d+)/$',
        views.chat_view,
        name='chat'
    ),
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),
]
