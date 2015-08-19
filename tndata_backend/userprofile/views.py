from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView
from django.views.generic.base import RedirectView

from utils.mixins import LoginRequiredMixin
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
        permissions = list(self.request.user.user_permissions.all())
        for group in self.request.user.groups.all():
            for perm in group.permissions.all():
                permissions.append(perm)
        context['permissions'] = sorted(permissions, key=lambda p: p.name)
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
