from django import http
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView

from . forms import EmailForm, SetNewPasswordForm
from . models import ResetToken


class PasswordResetRequestView(FormView):
    form_class = EmailForm
    template_name = "utils/password_reset_request.html"
    success_url = reverse_lazy('utils:password_reset_notification')

    def form_invalid(self, form):
        ctx = self.get_context_data(form=form)
        ctx['invalid_email'] = True
        return self.render_to_response(ctx)

    def form_valid(self, form):
        User = get_user_model()
        try:
            u = User.objects.get(email=form.cleaned_data['email_address'])
        except User.DoesNotExist:
            return self.form_invalid(form)

        # Set unusuable password and disable account
        u.set_unusable_password()
        u.is_active = False
        u.save()

        # Generate a token for this session and email the user.
        token = ResetToken(self.request, u.email)
        token.generate()
        token.send_email_notification()

        return redirect(self.success_url)


class PasswordResetNotificationView(TemplateView):
    template_name = "utils/password_reset_notification.html"


class SetNewPasswordView(FormView):
    form_class = SetNewPasswordForm
    template_name = "utils/set_new_password.html"
    success_url = reverse_lazy('utils:password_reset_complete')

    def get(self, request, *args, **kwargs):
        has_token = 'token' in kwargs and ResetToken.check(request, kwargs['token'])
        authenticated = request.user.is_authenticated

        if not has_token and not authenticated:
            # If there's no token, a user must be logged in to reset their pw.
            url = "{0}?next={1}".format(
                reverse_lazy("login"),
                reverse_lazy("utils:set_new_password")
            )
            return redirect(url)

        # Otherwise, the user should have requested this page with a token.
        if has_token or authenticated:
            return super(SetNewPasswordView, self).get(request, *args, **kwargs)
        return http.HttpResponseForbidden()

    def form_valid(self, form):
        # Update the user's password an re-enable their account
        email = ResetToken.get_email(self.request)
        if email is None and self.request.user.is_authenticated():
            email = self.request.user.email
        else:
            return redirect(reverse_lazy('utils:password_reset'))

        u = get_user_model().objects.get(email=email)
        u.set_password(form.cleaned_data['password'])
        u.is_active = True
        u.save()

        return redirect(self.success_url)


class PasswordResetCompleteView(TemplateView):
    template_name = "utils/password_reset_complete.html"
