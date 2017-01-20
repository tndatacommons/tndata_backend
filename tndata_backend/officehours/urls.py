from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^$',
        views.index,
        name='index'
    ),
    url(
        r'^login/$',
        views.login,
        name='login'
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
        r'^delete-courses/$',
        views.delete_courses,
        name='delete-courses'
    ),
    url(
        r'^delete-hours/$',
        views.delete_hours,
        name='delete-hours'
    ),
    url(
        r'^contact-info/$',
        views.contact_info,
        name='contact-info'
    ),
    url(
        r'^phone/$',
        views.phone_number,
        name='phone-number'
    ),
    url(
        r'^examples/$',
        views.mdl_examples,
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
    url(r'^about/$', views.AboutView.as_view(), name='about'),
    url(r'^contact/$', views.ContactView.as_view(), name='contact'),
    url(r'^help/$', views.HelpView.as_view(), name='help'),
]
