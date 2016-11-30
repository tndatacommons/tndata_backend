from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r'^$',
        views.IndexView.as_view(),
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
        r'^contact-info/$',
        views.contact_info,
        name='contact-info'
    ),
    url(
        r'^examples/$',
        views.ExamplesView.as_view(),
        name='examples'
    ),
]
