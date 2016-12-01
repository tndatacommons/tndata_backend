from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^$',
        views.index,
        name='index'
    ),
    url(
        r'^add-code/$',
        views.add_code,
        name='add-code'
    ),
    url(
        r'^add-hours/$',
        views.add_hours,
        name='add-hours'
    ),
    url(
        r'^add-course/$',
        views.add_course,
        name='add-course'
    ),
    url(
        r'^contact-info/$',
        views.contact_info,
        name='contact-info'
    ),
    url(
        r'^examples/$',
        views.ExamplesView.as_view(),
        name='examples'
    ),
    url(
        r'^schedule/(?P<pk>\d+)/share/$',
        views.share_course,
        name='share-course'
    ),
    url(
        r'^schedule/(?P<pk>\d+)/$',
        views.course_details,
        name='course-details'
    ),
    url(
        r'^schedule/$',
        views.schedule,
        name='schedule'
    ),
]
