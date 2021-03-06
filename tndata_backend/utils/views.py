import logging

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, FormView

from django_rq import job
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from goals.permissions import CONTENT_VIEWERS
from goals.models import Organization, Program

from userprofile.forms import UserForm
from . db import get_object_or_none
from . email import (
    send_new_user_request_notification_to_managers,
    send_new_enduser_welcome,
    send_new_user_welcome,
)
from . forms import EmailForm, SetNewPasswordForm
from . models import ResetToken
from . slack import post_message
from . user_utils import username_hash, get_client_ip


logger = logging.getLogger(__name__)


@job
def _enroll_user_in_program(user_id, program_id):
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        program = Program.objects.get(pk=program_id)
        for goal in program.auto_enrolled_goals.all():
            goal.enroll(user)
    except (User.DoesNotExist, Program.DoesNotExist):
        pass


def _setup_content_viewer(request, user, password):
    """Handle addional post-account-creation tasks for content viewers."""
    # Add them to the appropriate groups.
    for group in Group.objects.filter(name=CONTENT_VIEWERS):
        user.groups.add(group)

    # Log the user in & set an appropriate message.
    user = authenticate(username=user.username, password=password)
    login(request, user)
    messages.success(request, "Welcome! Your account has been created.")

    # Send some email notifications.
    send_new_user_request_notification_to_managers(user)
    send_new_user_welcome(user)

    # Ping slack so this doesn't go unnoticed.
    msg = (
        ":warning: Hey @bkmontgomery, {user} <{email}> just signed up as a "
        "content viewer. If necessary, update their permissions at: "
        "https://app.tndata.org/admin/auth/user/{id}/"
    )
    msg = msg.format(user=user.get_full_name(), email=user.email, id=user.id)
    post_message("#tech", msg)


def _setup_enduser(request, user, send_welcome_email=True):
    """Handle addional post-account-creation tasks for end-users."""
    User = get_user_model()

    # Check for any Organization & Program parameters (falling back to the
    # session values), and make the user an organization member and enroll
    # them in the Program's goals (if applicable).
    try:
        program_id = request.POST.get('program', request.session.get('program'))
        org_id = request.POST.get('organization', request.session.get('organization'))

        program = Program.objects.get(pk=program_id, organization__id=org_id)
        program.members.add(user)
        program.organization.members.add(user)
        _enroll_user_in_program.delay(user.id, program.id)

        # Don't make them go through onboarding
        user.userprofile.needs_onboarding = False
        user.userprofile.save()
    except Program.DoesNotExist:
        pass

    # Send some email notifications.
    if send_welcome_email:
        send_new_enduser_welcome(user)

    # Ping slack so this doesn't go unnoticed.
    num_users = User.objects.filter(is_active=True).count()
    msg = (
        ":exclamation: :point_right: {user} <{email}> just joined. That "
        "makes *{num_users}* active accounts."
    )
    msg = msg.format(
        user=user.get_full_name(), email=user.email, num_users=num_users
    )

    # Set an appropriate message.
    messages.success(request, "Welcome to Compass! Your account has been updated.")
    post_message("#tech", msg)


def signup(request, content_viewer=False, enduser=False):
    """This view handles user account creation. There are different scenarios
    for different types of users, as indicated by the keyword arguments to
    this function:

    - content_viewer: If True, the account will be created as a content viewer
      (ie. a user who may need access to the editing tools at some point). This
      user account will be automatically activated, logged in, and added to
      some groups.

        /utils/signup/

    - enduser: If True, the account will be created as if the user intends to
      download and use the mobile app. Their account will be created, and the
      user will be redirected to links to the mobile app(s).

        /join/

    For Endusers: The request may also include one or more parameters indicating
    the Organization & Program in which the user should be a member. For
    example: `/join/?organization=42&program=7`

        - Organization ID: The user will be added as a member of the specified
          organization.
        - Program ID: The user will be added as a member of the specified
          program and will be auto-enrolled in certain goals from the program

    """
    organization = get_object_or_none(Organization,
                                      pk=request.GET.get('organization'))
    program = get_object_or_none(Program, pk=request.GET.get('program'))

    # Stash these in a session for later... (see `confirm_join`).
    if organization or program:
        request.session['organization'] = organization.id if organization else None
        request.session['program'] = program.id if program else None

    # Set the template/redirection based on the type of user signup
    if enduser:
        template = 'utils/signup_enduser.html'
        redirect_to = 'join'
        login_url = "{}?next={}".format(reverse('login'), reverse('utils:confirm'))
    else:
        template = 'utils/signup_content_viewer.html'
        redirect_to = '/'
        login_url = "{}".format(reverse('login'))

    if request.method == "POST":
        form = UserForm(request.POST)
        password_form = SetNewPasswordForm(request.POST, prefix="pw")
        if form.is_valid() and password_form.is_valid():
            User = get_user_model()
            try:
                # Ensure the email isn't already tied to an account
                u = User.objects.get(email=form.cleaned_data['email'])
                messages.info(request, "It looks like you already have an "
                                       "account! Log in to continue.")
                return redirect(login_url)
            except User.DoesNotExist:
                # Create & activate the account, and do initial record-keeping
                u = form.save(commit=False)
                u.is_active = True
                u.username = username_hash(u.email)
                u.set_password(password_form.cleaned_data['password'])
                u.save()

                # Set their IP address.
                u.userprofile.ip_address = get_client_ip(request)
                u.userprofile.save()

                if content_viewer:
                    password = password_form.cleaned_data['password']
                    _setup_content_viewer(request, u, password)

                if enduser:
                    _setup_enduser(request, u)
                    redirect_to = reverse(redirect_to) + "?c=1"

                return redirect(redirect_to)
        else:
            messages.error(request, "We could not process your request. "
                                    "Please see the details, below.")
    elif enduser and request.user.is_authenticated():
        # Redirect to the confirmation page.
        return redirect(reverse("utils:confirm"))
    else:
        password_form = SetNewPasswordForm(prefix='pw')
        if organization:
            form = UserForm(for_organization=organization.name)
        elif program:
            form = UserForm(for_organization=program.organization.name)
        else:
            form = UserForm()

    # The following is a list of GET request variables that we'll pass along
    # as POST request vars once a user submits the login form.
    passthru_vars = ['organization', 'program']
    passthru_vars = {
        key: request.GET.get(key) for key in passthru_vars
        if request.GET.get(key)
    }

    context = {
        'organization': organization,
        'program': program,
        'passthru_vars': passthru_vars,
        'form': form,
        'password_form': password_form,
        'completed': bool(request.GET.get("c", False)),
        'android_url': settings.PLAY_APP_URL,
        'ios_url': settings.IOS_APP_URL,
        'login_url': login_url,
    }
    return render(request, template, context)


@login_required
def confirm_join(request):
    # Intermediary step for the signup--for users with existing accounts.
    org = get_object_or_none(Organization, pk=request.session.get('organization'))
    program = get_object_or_none(Program, pk=request.session.get('program'))

    if org is None and program is None:
        logger.warning("Org & Program are None in utils.views.confirm_join")

    # POST: enroll the user and redirect to a placeholder page.
    if request.POST and bool(request.POST.get('confirmed', False)):
        _setup_enduser(request, request.user, send_welcome_email=False)

        # Do a little cleanup. At this point, we shouldn't need these anymore.
        request.session.pop('organization', None)
        request.session.pop('program', None)

        return redirect(reverse("utils:confirm") + "?confirmed=1")

    template = 'utils/confirm_join.html'
    context = {
        'organization': org,
        'program': program,
        'confirmed': bool(request.GET.get('confirmed', False)),
    }
    return render(request, template, context)


@api_view(['POST'])
def reset_password(request):
    """This defines an API endpoint that allows users to reset their password.
    To reset a password, simply send a POST request with the following data:

        {email: 'YOUR EMAIL ADDRESS'}

    This will reset the user's password, and temporarily deactivate their
    accout. Instructions on reseting their password are emailed to them.

    Returns a 200 response upon success, and a 400 response on failure.

    ----

    """
    # TODO: WE should send a text message with a token in it & have the user
    # tap something to reset their email.

    # Validate the email
    form = EmailForm({'email_address': request.data.get('email')})
    if form.is_valid():
        logout(request)  # Sends the user_logged_out signal

        User = get_user_model()
        try:
            u = User.objects.get(email=form.cleaned_data['email_address'])

            # Set unusuable password and disable account
            u.set_unusable_password()
            u.is_active = False
            u.save()

            # Generate a token for this session and email the user.
            token = ResetToken(request, u.email)
            token.generate()
            token.send_email_notification()
            msg = {'message': 'Password Reset. Please check your email for instructions'}
            return Response(msg, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            pass

    error = {"error": "Invalid email address or account"}
    return Response(error, status=status.HTTP_400_BAD_REQUEST)


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
