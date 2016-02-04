from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^cancel-jobs/$', views.cancel_all_jobs, name='cancel-jobs'),
    url(r'^cancel-job/$', views.cancel_job, name='cancel-job'),
]
