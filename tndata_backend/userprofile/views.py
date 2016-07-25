from collections import Counter, OrderedDict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView
from django.views.generic.base import RedirectView
from django.utils import timezone

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
def report(request):
    """This is an all-in-one report about user accounts. Currently it lists
    information about:

    1. account creation.
    2. last login time.

    """
    days = 30  # how much history to display?

    User = get_user_model()
    now = timezone.now()
    since = now - timedelta(days=days)

    signups = User.objects.filter(date_joined__gte=since)
    signups = signups.datetimes('date_joined', 'day')
    signups = Counter([d.strftime("%Y-%m-%d") for d in signups])

    # Now that we have data, we need to zero-fill the missing parts.
    results = OrderedDict()
    for x in range(0, 30):
        x = (now - timedelta(days=x)).strftime("%Y-%m-%d")
        results[x] = signups.get(x, 0)
    signups = list(reversed(list(results.items())))

    # Last login in "days ago" buckets
    logins = {}
    for days in [1, 7, 30, 60, 90]:
        since = now - timedelta(days=days)
        logins[days] = User.objects.filter(last_login__lte=since).count()

    # > 90 days == 91
    since = now - timedelta(days=91)
    logins[91] = User.objects.filter(last_login__gte=since).count()

    # Male/Female count
    sexes = []
    for sex in UserProfile.objects.values_list('sex', flat=True):
        sexes.append(sex.lower() if sex else 'unknown')
    demographics = Counter(sexes)

    # Zip codes
    zipcodes = UserProfile.objects.values_list('zipcode', flat=True)
    zipcodes = Counter(z.strip() for z in zipcodes if z and z.isnumeric())
    zipcodes = list(sorted(zipcodes.items()))

    context = {
        'total_users': User.objects.all().count(),
        'demographics': demographics,
        'logins': logins,
        'signups': signups,
        'zipcodes': zipcodes,
    }
    return render(request, 'userprofile/report.html', context)


@user_passes_test(lambda u: u.is_authenticated() and u.is_staff)
def admin_remove_app_data(request):
    """An intermediary admin page that lets us choose which app data to
    remove for a user.

    - See: https://goo.gl/DrG4zl
    - And: https://app.tndata.org/admin/auth/user/

    """
    query = request.GET.get('q')  # The original query, if any
    ids = filter(None, request.GET.get('ids', '').split())
    User = get_user_model()
    users = User.objects.filter(id__in=ids)

    # Info to populate select fields for the types of objects to delete.
    object_types = [
        ('awards', 'Badges', "Delete all of the user's awarded Badges"),
        ('customgoal', 'Custom Goals', "Delete all of the user's custom goals"),
        ('customaction', 'Custom Actions',
            "Delete all of the user's custom actions"),
        ('usercompletedcustomaction', 'Completed Custom Actions',
            "Delete all of the user's history of completed custom actions"),
        ('customactionfeedback', 'Custom Action Feedback',
            "Delete all of the user-supplied feedback associated with their "
            "custom actions"),
        ('useraction', 'Actions', "Remove the user's selected Action data"),
        ('userbehavior', 'Behaviors', "Remove the user's selected Behavior data"),
        ('usergoal', 'Goals', "Remove the user's selected Goal data"),
        ('usercategory', 'Categories',
            "Remove the user's selected Categories. This will also force them"
            " through onboarding again"),
        ('trigger', 'Triggers', "Remove the user's custom triggers"),
        ('usercompletedaction', 'Completed Actions',
            "Remove the user's history of completed actions"),
        ('dailyprogress', 'Daily Progress',
            "Remove the user's daily progress snapshots"),
        ('packageenrollment', 'Package Enrollment',
            "Remove the user from all packages"),
        ('gcmmessage', 'GCM Messages', "Delete all queued GCM Messages"),
    ]

    if request.method == "POST":
        to_remove = [
            obj for obj, status in request.POST.items() if status == 'on'
        ]
        for user in users:
            for ot in to_remove:
                if ot == "awards":
                    user.badges.all().delete()
                else:
                    # e.g. call: user.useraction_set.all().delete()
                    attr = "{}_set".format(ot)
                    getattr(user, attr).all().delete()

        if 'usercategory' in to_remove:
            user.userprofile.needs_onboarding = True
            user.userprofile.save()

        messages.success(request, "The appliation data was cleared.")

        url = "/admin/auth/user/"
        if query:
            url = "{}?q={}".format(url, query)
        return HttpResponseRedirect(url)
    else:
        counts = {t[0]: 0 for t in object_types}
        for user in users:
            for ot in object_types:
                if ot[0] == "awards":
                    counts['awards'] = user.badges.count()
                else:
                    counts[ot[0]] += getattr(user, ot[0] + "_set").count()
        object_types = [t + (counts[t[0]], ) for t in object_types]

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
