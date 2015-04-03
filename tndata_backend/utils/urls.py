from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(
        r'^password/reset/complete/$',
        views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),
    url(
        r'^password/reset/sent/$',
        views.PasswordResetNotificationView.as_view(),
        name='password_reset_notification'
    ),
    url(
        r'^password/reset/$',
        views.PasswordResetRequestView.as_view(),
        name='password_reset'
    ),
    url(
        r'^password/(?P<token>.{32})/$',
        views.SetNewPasswordView.as_view(),
        name='set_new_password'
    ),
    url(
        r'^password/$',
        views.SetNewPasswordView.as_view(),
        name='set_new_password'
    ),
)
