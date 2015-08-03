from django import http
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, FormView

from userprofile.forms import UserForm
from . forms import EmailForm, SetNewPasswordForm
from . models import ResetToken
from . user_utils import username_hash

def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        password_form = SetNewPasswordForm(request.POST, prefix="pw")
        if form.is_valid() and password_form.is_valid():
            User = get_user_model()
            try:
                # Ensure the email isn't already tied to an account
                u = User.objects.get(email=form.cleaned_data['email'])
                messages.success(request, "It looks like you already have an "
                                          "account! Either log in, or reset "
                                          "your password to continue.")
                return redirect(reverse("login"))
            except User.DoesNotExist:
                u = form.save(commit=False)
                u.username = username_hash(u.email)
                u.is_active = False
                u.set_password(password_form.cleaned_data['password'])
                u.save()

                # Email admins about the new user.
                message = (
                    "We have a request for a new user account from the "
                    "following:\n\nName: {0}\nEmail: {1}\n\nTo activate this "
                    "account, visit:\n"
                    "https://app.tndata.org/admin/auth/user/{2}/\n\n"
                )
                message = message.format(u.get_full_name(), u.email, u.id)
                mail_admins("New User Request", message)

                return redirect(reverse("utils:signup") + "?c=1")
        else:
            messages.error(request, "We could not process your request. "
                                    "Please see the details, below.")
    else:
        form = UserForm()
        password_form = SetNewPasswordForm(prefix='pw')

    context = {
        'form': form,
        'password_form': password_form,
        'completed': bool(request.GET.get("c", False)),
    }
    return render(request, "utils/signup.html", context)


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
            # No email, but the user is logged in, so use theirs
            email = self.request.user.email
        elif email is None:
            # Otherwise, we need to ask them again.
            return redirect(reverse_lazy('utils:password_reset'))

        u = get_user_model().objects.get(email=email)
        u.set_password(form.cleaned_data['password'])
        u.is_active = True
        u.save()

        return redirect(self.get_success_url())


class PasswordResetCompleteView(TemplateView):
    template_name = "utils/password_reset_complete.html"


class FiveHundred(TemplateView):
    template_name = "500.html"


class FourOhFour(TemplateView):
    template_name = "404.html"


class FourOhThree(TemplateView):
    template_name = "403.html"
