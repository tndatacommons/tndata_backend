from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^send/$', views.send_message, name='send'),
    url(r'^cancel-jobs/$', views.cancel_all_jobs, name='cancel-jobs'),
    url(r'^cancel-job/$', views.cancel_job, name='cancel-job'),
    url(r'^(?P<message_id>\d+)/$', views.view_message, name='view'),
    url(
        r'^(?P<user_id>\d+)/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$',
        views.userqueue,
        name='userqueue'
    ),

]
