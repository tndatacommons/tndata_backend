from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView
from django.views.generic.base import RedirectView

from utils.mixins import LoginRequiredMixin
from utils.user_utils import get_all_permissions
from . forms import UserForm, UserProfileForm
from . models import UserProfile


class UserProfileRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect the user to their Profile's detail view."""
    def get_redirect_url(self, *args, **kwargs):
        return self.request.user.userprofile.get_absolute_url()


class UserProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    context_object_name = "profile"

    def get_queryset(self):
        """Ensure the queryset only includes the user's profile."""
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_all_permissions(self.request.user, sort=True)
        return context


@login_required
def update_profile(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk, user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        user_form = UserForm(request.POST, instance=request.user, prefix="user")
        if form.is_valid() and user_form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            user_form.save()
            messages.success(request, "Your profile has been updated")
            return redirect(profile.get_absolute_url())
        else:
            messages.error(request, "Your profile could not be saved")
    else:
        form = UserProfileForm(instance=profile)
        user_form = UserForm(instance=request.user, prefix="user")

    context = {'form': form, 'user_form': user_form}
    return render(request, "userprofile/userprofile_form.html", context)


@user_passes_test(lambda u: u.is_authenticated() and u.is_staff)
def admin_remove_app_data(request):
    """An intermediary admin page that lets us choose which app data to
    remove for a user.

    - See: https://goo.gl/DrG4zl
    - And: https://app.tndata.org/admin/auth/user/

    """
    ids = filter(None, request.GET.get('ids', '').split())
    User = get_user_model()
    users = User.objects.filter(id__in=ids)

    # Info to populate select fields for the types of objects to delete.
    object_types = [
        ('useraction', 'Actions', "Remove the user's selected Action data"),
        ('userbehavior', 'Behaviors', "Remove the user's selected Behavior data"),
        ('usergoal', 'Goals', "Remove the user's selected Goal data"),
        ('usercategory', 'Categories',
            "Remove the user's selected Categories. This will also force them"
            " through onboarding again"),
        ('trigger', 'Triggers', "Remove the user's custom triggers"),
        ('behaviorprogress', 'Behavior Progress',
            "Remove the user's behavior progress data"),
        ('goalprogress', 'Goal Progress',
            "Remove the user's goal progress data"),
        ('categoryprogress', 'Category Progress',
            "Remove the user's category progress data"),
        ('usercompletedaction', 'Completed Actions',
            "Remove the user's history of completed actions"),
        ('packageenrollment', 'Package Enrollment',
            "Remove the user from all packages"),
        ('gcmmessage', 'GCM Messages', "Delete all queued GCM Messages"),

        # TODO: Custom goals,
        # TODO: Custom actions,
        # TODO: Custom completed actions,
        # TODO: Custom feedback,
    ]

    if request.method == "POST":
        to_remove = [obj for obj, status in request.POST.items() if status == 'on']
        for user in users:
            for ot in to_remove:
                # e.g. call: user.useraction_set.all().delete()
                attr = "{}_set".format(ot)
                getattr(user, attr).all().delete()

            if 'usercategory' in to_remove:
                user.userprofile.needs_onboarding = True
                user.userprofile.save()

        return HttpResponseRedirect("/admin/auth/user/")

    # GET requests
    context = {
        'app_label': 'userprofile',
        'opts': {'app_label': 'userprofile'},
        'add': False,
        'adminform': None,
        'change': True,
        'title': "Remove the following App Data",
        'users': users,
        'object_types': object_types,
    }
    return render(request, "userprofile/admin_remove_app_data.html", context)
